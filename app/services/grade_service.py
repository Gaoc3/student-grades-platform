from __future__ import annotations

import uuid
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import GradeComponent, GradingPolicy, Student, StudentScore
from app.schemas import ComponentCreate, ComponentUpdate


def ensure_default_components(db: Session) -> None:
    # Check if we have any components
    existing = db.scalars(select(GradeComponent).limit(1)).first()
    if existing:
        return

    # Bologna Template defaults
    defaults = [
        # Course 1 - Coursework
        ("c1_midterm", "Midterm (Theory)", 1, "coursework", 15, 1),
        ("c1_prac_mid", "Midterm (Practical)", 1, "coursework", 15, 2),
        ("c1_quiz", "Quizzes", 1, "coursework", 10, 3),
        ("c1_attendance", "Attendance", 1, "coursework", 10, 4),
        # Course 1 - Final
        ("c1_final_prac", "Final (Practical)", 1, "final", 20, 5),
        ("c1_final_theory", "Final (Theory)", 1, "final", 30, 6),
        # Course 2 - Coursework
        ("c2_midterm", "Midterm (Theory)", 2, "coursework", 15, 1),
        ("c2_prac_mid", "Midterm (Practical)", 2, "coursework", 15, 2),
        ("c2_quiz", "Quizzes", 2, "coursework", 10, 3),
        ("c2_attendance", "Attendance", 2, "coursework", 10, 4),
        # Course 2 - Final
        ("c2_final_prac", "Final (Practical)", 2, "final", 20, 5),
        ("c2_final_theory", "Final (Theory)", 2, "final", 30, 6),
    ]

    for key, label, sem, cat, max_score, order in defaults:
        db.add(
            GradeComponent(
                component_key=key,
                label=label,
                semester=sem,
                category=cat,
                max_score=max_score,
                order_index=order,
            )
        )
    db.commit()


def create_component(db: Session, payload: ComponentCreate) -> GradeComponent:
    comp_key = f"comp_{uuid.uuid4().hex[:8]}"
    comp = GradeComponent(
        component_key=comp_key,
        label=payload.label,
        semester=payload.semester,
        category=payload.category,
        max_score=payload.max_score,
        order_index=payload.order_index,
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp


def update_component_service(db: Session, component_id: int, payload: ComponentUpdate) -> None:
    row = db.get(GradeComponent, component_id)
    if not row:
        raise HTTPException(status_code=404, detail="Component not found")

    row.label = payload.label
    row.semester = payload.semester
    row.category = payload.category
    row.max_score = payload.max_score
    row.order_index = payload.order_index
    db.commit()


def delete_component(db: Session, component_id: int) -> None:
    row = db.get(GradeComponent, component_id)
    if not row:
        raise HTTPException(status_code=404, detail="Component not found")
    
    # Also delete associated scores
    db.execute(delete(StudentScore).where(StudentScore.component_key == row.component_key))
    db.delete(row)
    db.commit()


def get_or_create_grading_policy(db: Session) -> GradingPolicy:
    policy = db.get(GradingPolicy, 1)
    if policy:
        return policy

    policy = GradingPolicy(id=1, coursework_total_max=50)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def update_coursework_total_max(db: Session, coursework_total_max: float) -> GradingPolicy:
    policy = get_or_create_grading_policy(db)
    policy.coursework_total_max = float(coursework_total_max)
    db.commit()
    db.refresh(policy)
    return policy


def grading_settings_snapshot(db: Session) -> dict:
    policy = get_or_create_grading_policy(db)
    return {
        "coursework_total_max": round(float(policy.coursework_total_max), 2),
    }


def gradebook_snapshot(db: Session) -> dict:
    components = db.scalars(
        select(GradeComponent).order_by(GradeComponent.semester, GradeComponent.category, GradeComponent.order_index, GradeComponent.id)
    ).all()
    students = db.scalars(select(Student).order_by(Student.full_name)).all()

    score_rows = db.scalars(select(StudentScore)).all()
    score_map: dict[int, dict[str, StudentScore]] = defaultdict(dict)
    for row in score_rows:
        score_map[row.student_id][row.component_key] = row

    rows = []
    for st in students:
        st_scores = score_map.get(st.id, {})
        
        # Calculate sums per semester and category
        sums = {
            "c1_coursework": 0.0,
            "c1_final": 0.0,
            "c2_coursework": 0.0,
            "c2_final": 0.0,
            "c1_total": 0.0,
            "c2_total": 0.0,
        }

        for c in components:
            score = st_scores.get(c.component_key)
            val = score.score if score else 0.0
            key = f"c{c.semester}_{c.category}"
            sums[key] += val
            sums[f"c{c.semester}_total"] += val

        rows.append(
            {
                "student": {"id": st.id, "full_name": st.full_name, "email": st.email},
                "scores": {k: {"score": v.score, "published": v.published} for k, v in st_scores.items()},
                "sums": {k: round(v, 2) for k, v in sums.items()},
            }
        )

    return {
        "components": [
            {
                "id": c.id,
                "component_key": c.component_key,
                "label": c.label,
                "semester": c.semester,
                "category": c.category,
                "max_score": c.max_score,
                "order_index": c.order_index,
            }
            for c in components
        ],
        "rows": rows,
    }


def upsert_scores(db: Session, student_id: int, scores: dict[str, float]) -> None:
    components = {c.component_key: c for c in db.scalars(select(GradeComponent)).all()}

    for key, value in scores.items():
        if key not in components:
            continue

        component = components[key]
        normalized = max(0, min(float(value), float(component.max_score)))

        row = db.scalar(
            select(StudentScore).where(StudentScore.student_id == student_id, StudentScore.component_key == key)
        )
        if row:
            row.score = normalized
            row.published = False
        else:
            db.add(
                StudentScore(
                    student_id=student_id,
                    component_key=key,
                    score=normalized,
                    published=False,
                )
            )

    db.commit()
