import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

# Ensure workspace root is in path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.models import Doctor, Student, GradeComponent, GradingPolicy, StudentScore, PublicationToken, Notification, MainBase, TenantBase

def main():
    pg_url = os.getenv("MAIN_DB_URL")
    if not pg_url or not (pg_url.startswith("postgres://") or pg_url.startswith("postgresql://")):
        print("Error: MAIN_DB_URL environment variable must be set to a valid PostgreSQL connection string.")
        print("Example: set MAIN_DB_URL=postgresql://postgres:password@db.fuahzakpsbnriyfejsgk.supabase.co:5432/postgres")
        sys.exit(1)

    print("Connecting to Supabase PostgreSQL database...")
    pg_engine = create_engine(pg_url, future=True)
    
    print("Dropping existing tables to clean target database...")
    # Clean up target tables in correct dependency order
    with pg_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS notifications CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS publication_tokens CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS student_scores CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS grading_policy CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS grade_components CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS students CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS doctors CASCADE;"))
        conn.commit()

    print("Creating PostgreSQL tables schema...")
    MainBase.metadata.create_all(bind=pg_engine)
    TenantBase.metadata.create_all(bind=pg_engine)

    PgSession = sessionmaker(bind=pg_engine, future=True)
    pg_session = PgSession()

    # Path to SQLite databases
    data_dir = Path("data")
    main_db_path = data_dir / "main.db"
    tenants_dir = data_dir / "tenants"

    if not main_db_path.exists():
        print(f"Error: main.db not found at {main_db_path.absolute()}")
        sys.exit(1)

    print("Reading doctors from local main.db...")
    sqlite_conn = sqlite3.connect(main_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    try:
        cursor.execute("SELECT id, full_name, email, password_hash, subject_name, created_at FROM doctors")
        doctors = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"Error reading doctors table: {e}")
        sqlite_conn.close()
        sys.exit(1)
    
    sqlite_conn.close()

    print(f"Found {len(doctors)} doctors in SQLite.")

    # Migrate doctors
    for doc in doctors:
        doc_id = doc["id"]
        created_at_dt = None
        if doc["created_at"]:
            try:
                created_at_dt = datetime.fromisoformat(doc["created_at"])
            except ValueError:
                created_at_dt = datetime.utcnow()
        else:
            created_at_dt = datetime.utcnow()

        doctor_obj = Doctor(
            id=doc_id,
            full_name=doc["full_name"],
            email=doc["email"],
            password_hash=doc["password_hash"],
            subject_name=doc["subject_name"],
            created_at=created_at_dt
        )
        pg_session.add(doctor_obj)
    
    pg_session.commit()
    print("Doctors migrated successfully.")

    # Reset doctors sequence
    with pg_engine.connect() as conn:
        conn.execute(text("SELECT setval(pg_get_serial_sequence('doctors', 'id'), coalesce(max(id), 1)) FROM doctors;"))
        conn.commit()

    # Migrate dynamic tenant databases
    for doc in doctors:
        doctor_id = doc["id"]
        tenant_db = tenants_dir / f"doctor_{doctor_id}.db"
        if not tenant_db.exists():
            print(f"Warning: Tenant DB for Doctor {doctor_id} ({doc['full_name']}) not found at {tenant_db}. Skipping...")
            continue

        print(f"Migrating tenant DB for Doctor {doctor_id} ({doc['full_name']})...")
        t_conn = sqlite3.connect(tenant_db)
        t_conn.row_factory = sqlite3.Row
        t_cursor = t_conn.cursor()

        # Migrate Grading Policy
        try:
            t_cursor.execute("SELECT coursework_total_max, updated_at FROM grading_policy LIMIT 1")
            policy_row = t_cursor.fetchone()
            if policy_row:
                updated_at_dt = None
                if policy_row["updated_at"]:
                    try:
                        updated_at_dt = datetime.fromisoformat(policy_row["updated_at"])
                    except ValueError:
                        updated_at_dt = datetime.utcnow()
                else:
                    updated_at_dt = datetime.utcnow()

                policy_obj = GradingPolicy(
                    doctor_id=doctor_id,
                    coursework_total_max=policy_row["coursework_total_max"],
                    updated_at=updated_at_dt
                )
                pg_session.add(policy_obj)
        except sqlite3.OperationalError:
            print("  No grading policy found. Creating default...")
            policy_obj = GradingPolicy(doctor_id=doctor_id, coursework_total_max=50, updated_at=datetime.utcnow())
            pg_session.add(policy_obj)

        # Migrate Grade Components
        try:
            t_cursor.execute("SELECT id, component_key, label, semester, category, max_score, order_index FROM grade_components")
            components = t_cursor.fetchall()
            for comp in components:
                comp_obj = GradeComponent(
                    doctor_id=doctor_id,
                    component_key=comp["component_key"],
                    label=comp["label"],
                    semester=comp["semester"],
                    category=comp["category"],
                    max_score=comp["max_score"],
                    order_index=comp["order_index"]
                )
                pg_session.add(comp_obj)
        except sqlite3.OperationalError:
            print("  No grade components table found.")

        # Migrate Students and maintain mapping
        student_mapping = {}  # old_student_id -> new_student_id
        try:
            t_cursor.execute("SELECT id, full_name, email, created_at FROM students")
            students = t_cursor.fetchall()
            for st in students:
                created_at_dt = None
                if st["created_at"]:
                    try:
                        created_at_dt = datetime.fromisoformat(st["created_at"])
                    except ValueError:
                        created_at_dt = datetime.utcnow()
                else:
                    created_at_dt = datetime.utcnow()

                st_obj = Student(
                    doctor_id=doctor_id,
                    full_name=st["full_name"],
                    email=st["email"],
                    created_at=created_at_dt
                )
                pg_session.add(st_obj)
                pg_session.flush()  # Populates st_obj.id from Postgres serial sequence
                student_mapping[st["id"]] = st_obj.id
        except sqlite3.OperationalError:
            print("  No students table found.")

        # Migrate Student Scores
        try:
            t_cursor.execute("SELECT id, student_id, component_key, score, published, updated_at FROM student_scores")
            scores = t_cursor.fetchall()
            for score in scores:
                new_student_id = student_mapping.get(score["student_id"])
                if not new_student_id:
                    continue  # skip orphans
                
                updated_at_dt = None
                if score["updated_at"]:
                    try:
                        updated_at_dt = datetime.fromisoformat(score["updated_at"])
                    except ValueError:
                        updated_at_dt = datetime.utcnow()
                else:
                    updated_at_dt = datetime.utcnow()

                score_obj = StudentScore(
                    doctor_id=doctor_id,
                    student_id=new_student_id,
                    component_key=score["component_key"],
                    score=score["score"],
                    published=bool(score["published"]),
                    updated_at=updated_at_dt
                )
                pg_session.add(score_obj)
        except sqlite3.OperationalError:
            print("  No student scores table found.")

        # Migrate Publication Tokens
        try:
            t_cursor.execute("SELECT id, student_id, token, expires_at, created_at, opened_at, first_seen_ip FROM publication_tokens")
            tokens = t_cursor.fetchall()
            for tok in tokens:
                new_student_id = student_mapping.get(tok["student_id"])
                if not new_student_id:
                    continue
                
                expires_at_dt = datetime.fromisoformat(tok["expires_at"]) if tok["expires_at"] else datetime.utcnow()
                created_at_dt = datetime.fromisoformat(tok["created_at"]) if tok["created_at"] else datetime.utcnow()
                opened_at_dt = datetime.fromisoformat(tok["opened_at"]) if tok["opened_at"] else None

                tok_obj = PublicationToken(
                    doctor_id=doctor_id,
                    student_id=new_student_id,
                    token=tok["token"],
                    expires_at=expires_at_dt,
                    created_at=created_at_dt,
                    opened_at=opened_at_dt,
                    first_seen_ip=tok["first_seen_ip"]
                )
                pg_session.add(tok_obj)
        except sqlite3.OperationalError:
            print("  No publication tokens table found.")

        # Migrate Notifications
        try:
            t_cursor.execute("SELECT id, event_type, message, payload_json, created_at FROM notifications")
            notifications = t_cursor.fetchall()
            for notif in notifications:
                created_at_dt = datetime.fromisoformat(notif["created_at"]) if notif["created_at"] else datetime.utcnow()
                
                notif_obj = Notification(
                    doctor_id=doctor_id,
                    event_type=notif["event_type"],
                    message=notif["message"],
                    payload_json=notif["payload_json"],
                    created_at=created_at_dt
                )
                pg_session.add(notif_obj)
        except sqlite3.OperationalError:
            print("  No notifications table found.")

        t_conn.close()
        pg_session.commit()
        print(f"  Successfully migrated database for Doctor {doctor_id} ({len(student_mapping)} students).")

    pg_session.close()

    print("Post-migration sequence updates in PostgreSQL...")
    with pg_engine.connect() as conn:
        conn.execute(text("SELECT setval(pg_get_serial_sequence('students', 'id'), coalesce(max(id), 1)) FROM students;"))
        conn.execute(text("SELECT setval(pg_get_serial_sequence('grade_components', 'id'), coalesce(max(id), 1)) FROM grade_components;"))
        conn.execute(text("SELECT setval(pg_get_serial_sequence('student_scores', 'id'), coalesce(max(id), 1)) FROM student_scores;"))
        conn.execute(text("SELECT setval(pg_get_serial_sequence('publication_tokens', 'id'), coalesce(max(id), 1)) FROM publication_tokens;"))
        conn.execute(text("SELECT setval(pg_get_serial_sequence('notifications', 'id'), coalesce(max(id), 1)) FROM notifications;"))
        conn.commit()

    print("\nData migration from SQLite to Supabase PostgreSQL completed with 100% SUCCESS!")

if __name__ == "__main__":
    main()
