from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_tenant_db
from app.models import GradeComponent, Student
from app.schemas import ComponentCreate, ComponentUpdate, GradingPolicyUpdate, ScorePatch
from app.services.grade_service import (
    create_component,
    delete_component,
    gradebook_snapshot,
    grading_settings_snapshot,
    update_component_service,
    update_coursework_total_max,
    upsert_scores,
)

router = APIRouter(prefix="/api", tags=["grades"])


@router.get("/components")
def list_components(db: Session = Depends(get_tenant_db)):
    rows = db.scalars(
        select(GradeComponent).order_by(GradeComponent.semester, GradeComponent.category, GradeComponent.order_index, GradeComponent.id)
    ).all()
    return [
        {
            "id": c.id,
            "component_key": c.component_key,
            "label": c.label,
            "semester": c.semester,
            "category": c.category,
            "max_score": c.max_score,
            "order_index": c.order_index,
        }
        for c in rows
    ]


@router.post("/components")
def add_component(payload: ComponentCreate, db: Session = Depends(get_tenant_db)):
    row = create_component(db, payload)
    return {"message": "Component created", "id": row.id}


@router.put("/components/{component_id}")
def update_component(component_id: int, payload: ComponentUpdate, db: Session = Depends(get_tenant_db)):
    update_component_service(db, component_id, payload)
    return {"message": "Component updated"}


@router.delete("/components/{component_id}")
def remove_component(component_id: int, db: Session = Depends(get_tenant_db)):
    delete_component(db, component_id)
    return {"message": "Component deleted"}


@router.get("/gradebook")
def gradebook(db: Session = Depends(get_tenant_db)):
    return gradebook_snapshot(db)


@router.get("/settings/grading")
def grading_settings(db: Session = Depends(get_tenant_db)):
    return grading_settings_snapshot(db)


@router.put("/settings/grading")
def update_grading_settings(payload: GradingPolicyUpdate, db: Session = Depends(get_tenant_db)):
    row = update_coursework_total_max(db, payload.coursework_total_max)
    return {"message": "Grading policy updated", "coursework_total_max": row.coursework_total_max}


@router.put("/students/{student_id}/scores")
def save_scores(student_id: int, payload: ScorePatch, db: Session = Depends(get_tenant_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    upsert_scores(db, student_id=student_id, scores=payload.scores)
    return {"message": "Scores saved"}
