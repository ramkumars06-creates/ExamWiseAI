"""
CRUD operations for all ExamWise AI models.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from . import models, schemas


# ---------------------------------------------------------------------------
# Student CRUD
# ---------------------------------------------------------------------------
def get_student(db: Session, student_id: int) -> Optional[models.Student]:
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_students(db: Session, skip: int = 0, limit: int = 100) -> List[models.Student]:
    return db.query(models.Student).offset(skip).limit(limit).all()


def create_student(db: Session, student: schemas.StudentCreate) -> models.Student:
    db_student = models.Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def update_student(db: Session, student_id: int, update: schemas.StudentUpdate) -> Optional[models.Student]:
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_student, field, value)
    db.commit()
    db.refresh(db_student)
    return db_student


# ---------------------------------------------------------------------------
# Subject CRUD
# ---------------------------------------------------------------------------
def get_subject(db: Session, subject_id: int) -> Optional[models.Subject]:
    return db.query(models.Subject).filter(models.Subject.id == subject_id).first()


def get_subjects_by_student(db: Session, student_id: int) -> List[models.Subject]:
    return db.query(models.Subject).filter(models.Subject.student_id == student_id).all()


def create_subject(db: Session, subject: schemas.SubjectCreate) -> models.Subject:
    db_subject = models.Subject(**subject.model_dump())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


def update_subject(db: Session, subject_id: int, update: schemas.SubjectUpdate) -> Optional[models.Subject]:
    db_subject = get_subject(db, subject_id)
    if not db_subject:
        return None
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_subject, field, value)
    db.commit()
    db.refresh(db_subject)
    return db_subject


def delete_subject(db: Session, subject_id: int) -> bool:
    db_subject = get_subject(db, subject_id)
    if not db_subject:
        return False
    db.delete(db_subject)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Unit CRUD
# ---------------------------------------------------------------------------
def get_unit(db: Session, unit_id: int) -> Optional[models.Unit]:
    return db.query(models.Unit).filter(models.Unit.id == unit_id).first()


def get_units_by_subject(db: Session, subject_id: int) -> List[models.Unit]:
    return db.query(models.Unit).filter(models.Unit.subject_id == subject_id).order_by(models.Unit.order_index).all()


def create_unit(db: Session, unit: schemas.UnitCreate) -> models.Unit:
    db_unit = models.Unit(**unit.model_dump())
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit


# ---------------------------------------------------------------------------
# Topic CRUD
# ---------------------------------------------------------------------------
def get_topic(db: Session, topic_id: int) -> Optional[models.Topic]:
    return db.query(models.Topic).filter(models.Topic.id == topic_id).first()


def get_topics_by_unit(db: Session, unit_id: int) -> List[models.Topic]:
    return db.query(models.Topic).filter(models.Topic.unit_id == unit_id).all()


def get_topics_by_subject(db: Session, subject_id: int) -> List[models.Topic]:
    """Retrieve all topics belonging to a subject (via units)."""
    return (
        db.query(models.Topic)
        .join(models.Unit, models.Topic.unit_id == models.Unit.id)
        .filter(models.Unit.subject_id == subject_id)
        .all()
    )


def create_topic(db: Session, topic: schemas.TopicCreate) -> models.Topic:
    db_topic = models.Topic(**topic.model_dump())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


def update_topic(db: Session, topic_id: int, update: schemas.TopicUpdate) -> Optional[models.Topic]:
    db_topic = get_topic(db, topic_id)
    if not db_topic:
        return None
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_topic, field, value)
    db.commit()
    db.refresh(db_topic)
    return db_topic


def delete_topic(db: Session, topic_id: int) -> bool:
    db_topic = get_topic(db, topic_id)
    if not db_topic:
        return False
    db.delete(db_topic)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Assessment CRUD
# ---------------------------------------------------------------------------
def get_assessment(db: Session, assessment_id: int) -> Optional[models.Assessment]:
    return db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()


def get_assessments_by_student(db: Session, student_id: int) -> List[models.Assessment]:
    return (
        db.query(models.Assessment)
        .filter(models.Assessment.student_id == student_id)
        .order_by(models.Assessment.completed_at.desc())
        .all()
    )


def create_assessment(db: Session, assessment: schemas.AssessmentCreate) -> models.Assessment:
    db_assessment = models.Assessment(**assessment.model_dump())
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment


def update_assessment(db: Session, assessment_id: int, **kwargs) -> Optional[models.Assessment]:
    db_assessment = get_assessment(db, assessment_id)
    if not db_assessment:
        return None
    for field, value in kwargs.items():
        setattr(db_assessment, field, value)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment


def add_assessment_question(db: Session, question_data: dict) -> models.AssessmentQuestion:
    db_q = models.AssessmentQuestion(**question_data)
    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    return db_q


# ---------------------------------------------------------------------------
# StudySession CRUD
# ---------------------------------------------------------------------------
def get_study_session(db: Session, session_id: int) -> Optional[models.StudySession]:
    return db.query(models.StudySession).filter(models.StudySession.id == session_id).first()


def get_study_sessions_by_student(db: Session, student_id: int) -> List[models.StudySession]:
    return (
        db.query(models.StudySession)
        .filter(models.StudySession.student_id == student_id)
        .order_by(models.StudySession.scheduled_start)
        .all()
    )


def create_study_session(db: Session, session: schemas.StudySessionCreate) -> models.StudySession:
    db_session = models.StudySession(**session.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def update_study_session(db: Session, session_id: int, update: schemas.StudySessionUpdate) -> Optional[models.StudySession]:
    db_session = get_study_session(db, session_id)
    if not db_session:
        return None
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_session, field, value)
    db.commit()
    db.refresh(db_session)
    return db_session


# ---------------------------------------------------------------------------
# StudyPlan CRUD
# ---------------------------------------------------------------------------
def get_active_plan(db: Session, student_id: int) -> Optional[models.StudyPlan]:
    return (
        db.query(models.StudyPlan)
        .filter(models.StudyPlan.student_id == student_id, models.StudyPlan.status == "active")
        .order_by(models.StudyPlan.version.desc())
        .first()
    )


def get_plan_history(db: Session, student_id: int) -> List[models.StudyPlan]:
    return (
        db.query(models.StudyPlan)
        .filter(models.StudyPlan.student_id == student_id)
        .order_by(models.StudyPlan.version.desc())
        .all()
    )


def create_study_plan(db: Session, plan: schemas.StudyPlanCreate) -> models.StudyPlan:
    # Archive existing active plans
    db.query(models.StudyPlan).filter(
        models.StudyPlan.student_id == plan.student_id,
        models.StudyPlan.status == "active"
    ).update({"status": "archived"})
    db.commit()

    db_plan = models.StudyPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


# ---------------------------------------------------------------------------
# ActivityLog CRUD
# ---------------------------------------------------------------------------
def log_activity(db: Session, student_id: int, event_type: str, description: str = None, metadata_json: str = None) -> models.ActivityLog:
    log = models.ActivityLog(
        student_id=student_id,
        event_type=event_type,
        description=description,
        metadata_json=metadata_json,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_activity_logs(db: Session, student_id: int, limit: int = 50) -> List[models.ActivityLog]:
    return (
        db.query(models.ActivityLog)
        .filter(models.ActivityLog.student_id == student_id)
        .order_by(models.ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )


# ---------------------------------------------------------------------------
# AgentRun CRUD
# ---------------------------------------------------------------------------
def create_agent_run(db: Session, workflow_id: str, agent_name: str, input_summary: str = None) -> models.AgentRun:
    run = models.AgentRun(
        workflow_id=workflow_id,
        agent_name=agent_name,
        status="running",
        input_summary=input_summary,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def update_agent_run(db: Session, run_id: int, status: str, output_summary: str = None, error_message: str = None) -> Optional[models.AgentRun]:
    run = db.query(models.AgentRun).filter(models.AgentRun.id == run_id).first()
    if not run:
        return None
    run.status = status
    if output_summary:
        run.output_summary = output_summary
    if error_message:
        run.error_message = error_message
    db.commit()
    db.refresh(run)
    return run
