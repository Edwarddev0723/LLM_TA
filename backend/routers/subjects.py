"""
Subjects and Units router for the AI Math Tutor system.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from backend.models import get_db, Subject, Unit

router = APIRouter(tags=["Subjects"])


@router.get("/subjects")
async def get_subjects(db: DBSession = Depends(get_db)):
    """Get all subjects."""
    subjects = db.query(Subject).all()
    
    return {
        "subjects": [
            {
                "id": s.id,
                "subject_name": s.subject_name,
                "description": s.description
            }
            for s in subjects
        ]
    }


@router.get("/units")
async def get_units(db: DBSession = Depends(get_db)):
    """Get all units with subject information."""
    units = db.query(Unit).join(Subject).all()
    
    return {
        "units": [
            {
                "id": u.id,
                "unit_name": u.unit_name,
                "subject_id": u.subject_id,
                "subject_name": u.subject.subject_name
            }
            for u in units
        ]
    }
