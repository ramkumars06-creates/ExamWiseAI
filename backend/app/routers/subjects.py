"""
Subject, Unit, and Topic CRUD endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas

router = APIRouter(tags=["subjects"])


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------
@router.get("/api/subjects", response_model=List[schemas.SubjectResponse])
def list_subjects(student_id: int = 1, db: Session = Depends(get_db)):
    """List all subjects for a student."""
    return crud.get_subjects_by_student(db, student_id)


@router.post("/api/subjects", response_model=schemas.SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(subject: schemas.SubjectCreate, db: Session = Depends(get_db)):
    """Create a new subject."""
    db_subject = crud.create_subject(db, subject)
    crud.log_activity(db, subject.student_id, "subject_created", f"Subject '{db_subject.name}' added.")
    return db_subject


@router.get("/api/subjects/{subject_id}", response_model=schemas.SubjectResponse)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    """Get a subject by ID."""
    db_subject = crud.get_subject(db, subject_id)
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return db_subject


@router.patch("/api/subjects/{subject_id}", response_model=schemas.SubjectResponse)
def update_subject(subject_id: int, update: schemas.SubjectUpdate, db: Session = Depends(get_db)):
    """Update a subject."""
    db_subject = crud.update_subject(db, subject_id, update)
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return db_subject


@router.delete("/api/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    """Delete a subject and all its content."""
    success = crud.delete_subject(db, subject_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subject not found")


@router.get("/api/subjects/{subject_id}/topics", response_model=List[schemas.TopicResponse])
def get_subject_topics(subject_id: int, db: Session = Depends(get_db)):
    """Get all topics for a subject."""
    db_subject = crud.get_subject(db, subject_id)
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return crud.get_topics_by_subject(db, subject_id)


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------
@router.post("/api/units", response_model=schemas.UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(unit: schemas.UnitCreate, db: Session = Depends(get_db)):
    """Create a unit for a subject."""
    db_subject = crud.get_subject(db, unit.subject_id)
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return crud.create_unit(db, unit)


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------
@router.post("/api/topics", response_model=schemas.TopicResponse, status_code=status.HTTP_201_CREATED)
def create_topic(topic: schemas.TopicCreate, db: Session = Depends(get_db)):
    """Create a topic under a unit."""
    from .. import models
    unit = db.query(models.Unit).filter(models.Unit.id == topic.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return crud.create_topic(db, topic)


@router.patch("/api/topics/{topic_id}", response_model=schemas.TopicResponse)
def update_topic(topic_id: int, update: schemas.TopicUpdate, db: Session = Depends(get_db)):
    """Update a topic."""
    db_topic = crud.update_topic(db, topic_id, update)
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return db_topic


@router.delete("/api/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    """Delete a topic."""
    success = crud.delete_topic(db, topic_id)
    if not success:
        raise HTTPException(status_code=404, detail="Topic not found")
