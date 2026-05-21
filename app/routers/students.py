from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_tenant_db
from app.models import Student
from app.schemas import StudentCreate, StudentUpdate

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("")
def list_students(search: str | None = None, db: Session = Depends(get_tenant_db)):
    stmt = select(Student).order_by(Student.full_name)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(Student.full_name.ilike(pattern))

    students = db.scalars(stmt).all()
    return [{"id": s.id, "full_name": s.full_name, "email": s.email} for s in students]


@router.post("")
def create_student(payload: StudentCreate, db: Session = Depends(get_tenant_db)):
    student = Student(full_name=payload.full_name.strip(), email=payload.email)
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"id": student.id, "full_name": student.full_name, "email": student.email}


@router.put("/{student_id}")
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_tenant_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if payload.full_name is not None:
        student.full_name = payload.full_name.strip()
    if payload.email is not None:
        student.email = payload.email

    db.commit()
    return {"message": "Updated"}


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_tenant_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()
    return {"message": "Deleted"}


@router.post("/import-emails")
async def import_name_email_map(file: UploadFile = File(...), db: Session = Depends(get_tenant_db)):
    if not file.filename.lower().endswith((".txt", ".csv")):
        raise HTTPException(status_code=400, detail="Only .txt or .csv allowed")

    content = (await file.read()).decode("utf-8", errors="ignore")

    updated = 0
    created = 0
    skipped = 0

    existing_by_name = {
        s.full_name.strip().lower(): s
        for s in db.scalars(select(Student)).all()
    }

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            skipped += 1
            continue

        name, email = [x.strip() for x in line.split(":", 1)]
        if not name or "@" not in email:
            skipped += 1
            continue

        key = name.lower()
        st = existing_by_name.get(key)
        if st:
            st.email = email
            updated += 1
        else:
            st = Student(full_name=name, email=email)
            db.add(st)
            existing_by_name[key] = st
            created += 1

    db.commit()

    return {"message": "Import finished", "created": created, "updated": updated, "skipped": skipped}
