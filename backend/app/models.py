"""
SQLAlchemy ORM models for ExamWise AI
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    institution: Mapped[Optional[str]] = mapped_column(String(300))
    program: Mapped[Optional[str]] = mapped_column(String(200))
    semester: Mapped[Optional[int]] = mapped_column(Integer)
    preferred_study_hours: Mapped[float] = mapped_column(Float, default=4.0)
    preferred_study_time: Mapped[Optional[str]] = mapped_column(String(50))  # morning/afternoon/evening
    learning_preferences: Mapped[Optional[str]] = mapped_column(Text)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    demo_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    subjects: Mapped[List["Subject"]] = relationship("Subject", back_populates="student", cascade="all, delete-orphan")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="student", cascade="all, delete-orphan")
    study_sessions: Mapped[List["StudySession"]] = relationship("StudySession", back_populates="student", cascade="all, delete-orphan")
    study_plans: Mapped[List["StudyPlan"]] = relationship("StudyPlan", back_populates="student", cascade="all, delete-orphan")
    activity_logs: Mapped[List["ActivityLog"]] = relationship("ActivityLog", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student id={self.id} name={self.name}>"


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50))
    exam_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    confidence_level: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    color: Mapped[Optional[str]] = mapped_column(String(20))  # hex color for UI
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student: Mapped["Student"] = relationship("Student", back_populates="subjects")
    units: Mapped[List["Unit"]] = relationship("Unit", back_populates="subject", cascade="all, delete-orphan", order_by="Unit.order_index")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="subject", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subject id={self.id} name={self.name}>"


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[Optional[str]] = mapped_column(Text)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="units")
    topics: Mapped[List["Topic"]] = relationship("Topic", back_populates="unit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Unit id={self.id} name={self.name}>"


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(400), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    exam_importance: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=60)
    mastery_estimate: Mapped[Optional[float]] = mapped_column(Float)  # 0-1, None = unassessed
    completion_status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started/in_progress/completed
    last_studied_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    priority_score: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    unit: Mapped["Unit"] = relationship("Unit", back_populates="topics")
    study_sessions: Mapped[List["StudySession"]] = relationship("StudySession", back_populates="topic")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="topic")

    def __repr__(self):
        return f"<Topic id={self.id} title={self.title}>"


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"))
    topic_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("topics.id", ondelete="SET NULL"))
    score: Mapped[Optional[float]] = mapped_column(Float)  # 0-1
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/completed/abandoned
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_minutes: Mapped[Optional[float]] = mapped_column(Float)

    student: Mapped["Student"] = relationship("Student", back_populates="assessments")
    subject: Mapped[Optional["Subject"]] = relationship("Subject", back_populates="assessments")
    topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="assessments")
    questions: Mapped[List["AssessmentQuestion"]] = relationship("AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Assessment id={self.id} score={self.score}>"


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assessment_id: Mapped[int] = mapped_column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options_json: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of option strings
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)
    student_answer: Mapped[Optional[str]] = mapped_column(String(500))
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    topic_tag: Mapped[Optional[str]] = mapped_column(String(200))
    difficulty: Mapped[Optional[str]] = mapped_column(String(20))

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="questions")

    def __repr__(self):
        return f"<AssessmentQuestion id={self.id}>"


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("topics.id", ondelete="SET NULL"))
    scheduled_start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    planned_minutes: Mapped[int] = mapped_column(Integer, default=60)
    actual_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")  # scheduled/in_progress/completed/missed/skipped
    self_reported_understanding: Mapped[Optional[float]] = mapped_column(Float)  # 0-1
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    student: Mapped["Student"] = relationship("Student", back_populates="study_sessions")
    topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="study_sessions")

    def __repr__(self):
        return f"<StudySession id={self.id} status={self.status}>"


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/archived/draft
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revision_reason: Mapped[Optional[str]] = mapped_column(Text)
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    summary_json: Mapped[Optional[str]] = mapped_column(Text)  # JSON summary

    student: Mapped["Student"] = relationship("Student", back_populates="study_plans")

    def __repr__(self):
        return f"<StudyPlan id={self.id} version={self.version} status={self.status}>"


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[Optional[str]] = mapped_column(String(100))
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running/completed/failed
    input_summary: Mapped[Optional[str]] = mapped_column(Text)
    output_summary: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    def __repr__(self):
        return f"<AgentRun id={self.id} agent={self.agent_name} status={self.status}>"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # event types: session_completed, session_missed, assessment_completed, plan_generated, plan_revised, topic_updated, milestone_reached
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student: Mapped["Student"] = relationship("Student", back_populates="activity_logs")

    def __repr__(self):
        return f"<ActivityLog id={self.id} event={self.event_type}>"
