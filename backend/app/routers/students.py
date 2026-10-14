"""
Student CRUD endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas

router = APIRouter(prefix="/api/students", tags=["students"])


@router.post("", response_model=schemas.StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    """Create a new student profile."""
    db_student = crud.create_student(db, student)
    crud.log_activity(db, db_student.id, "student_created", f"Student '{db_student.name}' created.")
    return db_student


@router.get("/{student_id}", response_model=schemas.StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Get student by ID."""
    db_student = crud.get_student(db, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student


@router.patch("/{student_id}", response_model=schemas.StudentResponse)
def update_student(student_id: int, update: schemas.StudentUpdate, db: Session = Depends(get_db)):
    """Partially update a student profile."""
    db_student = crud.update_student(db, student_id, update)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    crud.log_activity(db, student_id, "student_updated", "Student profile updated.")
    return db_student
