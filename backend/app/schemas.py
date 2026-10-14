"""
Pydantic v2 schemas for ExamWise AI API
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


# ──────────────────────────────────────────────
# Student Schemas
# ──────────────────────────────────────────────
class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    institution: Optional[str] = None
    program: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=12)
    preferred_study_hours: float = Field(4.0, ge=0.5, le=16.0)
    preferred_study_time: Optional[str] = None
    learning_preferences: Optional[str] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    institution: Optional[str] = None
    program: Optional[str] = None
    semester: Optional[int] = None
    preferred_study_hours: Optional[float] = None
    preferred_study_time: Optional[str] = None
    learning_preferences: Optional[str] = None
    onboarding_complete: Optional[bool] = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    institution: Optional[str] = None
    program: Optional[str] = None
    semester: Optional[int] = None
    preferred_study_hours: float
    preferred_study_time: Optional[str] = None
    learning_preferences: Optional[str] = None
    onboarding_complete: bool
    demo_mode: bool
    created_at: datetime


# ──────────────────────────────────────────────
# Subject Schemas
# ──────────────────────────────────────────────
class SubjectCreate(BaseModel):
    student_id: int
    name: str = Field(..., min_length=1, max_length=300)
    code: Optional[str] = None
    exam_date: Optional[datetime] = None
    difficulty: float = Field(0.5, ge=0.0, le=1.0)
    confidence_level: float = Field(0.5, ge=0.0, le=1.0)
    color: Optional[str] = None


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    exam_date: Optional[datetime] = None
    difficulty: Optional[float] = None
    confidence_level: Optional[float] = None
    color: Optional[str] = None


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    name: str
    code: Optional[str] = None
    exam_date: Optional[datetime] = None
    difficulty: float
    confidence_level: float
    color: Optional[str] = None
    created_at: datetime


class SubjectWithUnits(SubjectResponse):
    units: List["UnitWithTopics"] = []


# ──────────────────────────────────────────────
# Unit Schemas
# ──────────────────────────────────────────────
class UnitCreate(BaseModel):
    subject_id: int
    name: str = Field(..., min_length=1, max_length=300)
    order_index: int = 0
    description: Optional[str] = None


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject_id: int
    name: str
    order_index: int
    description: Optional[str] = None


class UnitWithTopics(UnitResponse):
    topics: List["TopicResponse"] = []


# ──────────────────────────────────────────────
# Topic Schemas
# ──────────────────────────────────────────────
class TopicCreate(BaseModel):
    unit_id: int
    title: str = Field(..., min_length=1, max_length=400)
    description: Optional[str] = None
    difficulty: float = Field(0.5, ge=0.0, le=1.0)
    exam_importance: float = Field(0.5, ge=0.0, le=1.0)
    estimated_minutes: int = Field(60, ge=5, le=600)
    mastery_estimate: Optional[float] = Field(None, ge=0.0, le=1.0)
    completion_status: str = "not_started"
    notes: Optional[str] = None


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[float] = None
    exam_importance: Optional[float] = None
    estimated_minutes: Optional[int] = None
    mastery_estimate: Optional[float] = None
    completion_status: Optional[str] = None
    last_studied_at: Optional[datetime] = None
    notes: Optional[str] = None


class TopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    unit_id: int
    title: str
    description: Optional[str] = None
    difficulty: float
    exam_importance: float
    estimated_minutes: int
    mastery_estimate: Optional[float] = None
    completion_status: str
    last_studied_at: Optional[datetime] = None
    priority_score: Optional[float] = None
    notes: Optional[str] = None


# ──────────────────────────────────────────────
# Assessment Schemas
# ──────────────────────────────────────────────
class AssessmentStart(BaseModel):
    student_id: int
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    question_count: int = Field(10, ge=1, le=50)
    difficulty: Optional[str] = None  # easy/medium/hard/mixed


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_text: str
    options_json: Optional[str] = None
    explanation: Optional[str] = None
    topic_tag: Optional[str] = None
    difficulty: Optional[str] = None


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    score: Optional[float] = None
    total_questions: int
    correct_answers: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    questions: List[QuestionResponse] = []


class AnswerSubmit(BaseModel):
    question_id: int
    answer: str


class AssessmentSubmit(BaseModel):
    answers: List[AnswerSubmit]


class AssessmentResult(BaseModel):
    assessment_id: int
    score: float
    correct_answers: int
    total_questions: int
    percentage: float
    topic_performance: Dict[str, float] = {}
    weak_areas: List[str] = []
    recommendations: List[str] = []
    mastery_updated: bool = False


# ──────────────────────────────────────────────
# Study Session Schemas
# ──────────────────────────────────────────────
class StudySessionCreate(BaseModel):
    student_id: int
    topic_id: Optional[int] = None
    scheduled_start: Optional[datetime] = None
    planned_minutes: int = Field(60, ge=5, le=600)


class StudySessionUpdate(BaseModel):
    status: Optional[str] = None
    actual_minutes: Optional[int] = None
    self_reported_understanding: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None


class StudySessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    topic_id: Optional[int] = None
    scheduled_start: Optional[datetime] = None
    planned_minutes: int
    actual_minutes: Optional[int] = None
    status: str
    self_reported_understanding: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class StudySessionWithTopic(StudySessionResponse):
    topic: Optional[TopicResponse] = None


# ──────────────────────────────────────────────
# Study Plan Schemas
# ──────────────────────────────────────────────
class PlanGenerateRequest(BaseModel):
    student_id: int
    revision_reason: Optional[str] = None


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    version: int
    status: str
    created_at: datetime
    revision_reason: Optional[str] = None
    total_sessions: int


# ──────────────────────────────────────────────
# Analytics Schemas
# ──────────────────────────────────────────────
class OverviewMetrics(BaseModel):
    total_topics: int
    completed_topics: int
    syllabus_completion: float
    mastered_topics: int
    topics_mastery_rate: float
    study_hours_this_week: float
    planned_hours_this_week: float
    upcoming_exams: int
    streak_days: int
    missed_sessions: int
    total_assessments: int
    avg_assessment_score: Optional[float] = None


class SubjectProgress(BaseModel):
    subject_id: int
    subject_name: str
    subject_code: Optional[str] = None
    total_topics: int
    completed_topics: int
    completion_rate: float
    avg_mastery: Optional[float] = None
    exam_date: Optional[datetime] = None
    days_until_exam: Optional[int] = None


class DailyStudyData(BaseModel):
    date: str
    planned_minutes: int
    actual_minutes: int
    sessions_count: int


class ProgressResponse(BaseModel):
    subjects: List[SubjectProgress] = []
    daily_study: List[DailyStudyData] = []
    mastery_distribution: Dict[str, int] = {}  # strong/moderate/weak/unassessed counts
    assessment_history: List[Dict[str, Any]] = []


# ──────────────────────────────────────────────
# Readiness Schemas
# ──────────────────────────────────────────────
class SubjectReadiness(BaseModel):
    subject_id: int
    subject_name: str
    exam_date: Optional[datetime] = None
    days_remaining: Optional[int] = None
    syllabus_coverage: float
    topic_mastery: float
    assessment_performance: Optional[float] = None
    overall_readiness: Optional[float] = None
    confidence_level: str  # low/medium/high/insufficient_data
    outstanding_topics: List[str] = []
    estimated_study_hours_remaining: float
    available_study_hours: float
    recommendation: str
    insufficient_data: bool = False


# ──────────────────────────────────────────────
# Coach Schemas
# ──────────────────────────────────────────────
class CoachMessage(BaseModel):
    student_id: int
    message: str
    context: Optional[Dict[str, Any]] = None


class CoachResponse(BaseModel):
    reply: str
    intent: str
    actions: List[Dict[str, Any]] = []
    data: Optional[Dict[str, Any]] = None
    demo_mode: bool = True


# ──────────────────────────────────────────────
# Syllabus Schemas
# ──────────────────────────────────────────────
class ExtractedUnit(BaseModel):
    name: str
    topics: List[str] = []


class ExtractedSubject(BaseModel):
    name: str
    units: List[ExtractedUnit] = []
    raw_text: Optional[str] = None


class SyllabusExtractResponse(BaseModel):
    success: bool
    filename: str
    page_count: int
    extracted_subjects: List[ExtractedSubject] = []
    raw_text_preview: str = ""
    warnings: List[str] = []
    error: Optional[str] = None


# ──────────────────────────────────────────────
# Agent Run Schemas
# ──────────────────────────────────────────────
class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    workflow_id: Optional[str] = None
    agent_name: str
    status: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# ──────────────────────────────────────────────
# Activity Log Schemas
# ──────────────────────────────────────────────
class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    event_type: str
    description: str
    metadata_json: Optional[str] = None
    created_at: datetime


# Resolve forward references
SubjectWithUnits.model_rebuild()
UnitWithTopics.model_rebuild()
