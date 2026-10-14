"""
Study plans and study sessions endpoints.
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas, models
from ..engines.scheduler import generate_schedule
from ..engines.priority import calculate_priority_score

router = APIRouter(tags=["plans"])


def _get_student_or_404(db: Session, student_id: int) -> models.Student:
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return student


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------
@router.post("/api/plans/generate")
def generate_plan(req: schemas.PlanGenerateRequest, db: Session = Depends(get_db)):
    """Generate a new study plan for a student."""
    student = _get_student_or_404(db, req.student_id)

    subjects = crud.get_subjects_by_student(db, req.student_id)
    if not subjects:
        raise HTTPException(status_code=422, detail="No subjects found. Add subjects before generating a plan.")

    # Gather all topics with their subject info
    all_topics = []
    subject_map = {}
    for subj in subjects:
        subject_map[subj.id] = subj
        topics = crud.get_topics_by_subject(db, subj.id)
        for t in topics:
            all_topics.append({
                "id": t.id,
                "title": t.title,
                "subject_id": subj.id,
                "unit_id": t.unit_id,
                "estimated_minutes": t.estimated_minutes,
                "mastery_estimate": t.mastery_estimate,
                "exam_importance": t.exam_importance,
                "difficulty": t.difficulty,
                "status": t.status,
                "last_studied_at": t.last_studied_at,
                "completion_status": t.completion_status,
            })

    if not all_topics:
        raise HTTPException(status_code=422, detail="No topics found. Add topics before generating a plan.")

    subjects_dicts = [
        {
            "id": s.id,
            "name": s.name,
            "exam_date": s.exam_date,
        }
        for s in subjects
    ]

    preferences = {
        "daily_hours": student.preferred_study_hours or 4.0,
        "preferred_study_time": student.preferred_study_time or "morning",
        "start_date": datetime.utcnow(),
    }

    # Generate schedule
    session_dicts = generate_schedule(
        student_id=req.student_id,
        subjects=subjects_dicts,
        topics=all_topics,
        preferences=preferences,
    )

    # Archive old active plans
    db.query(models.StudyPlan).filter(
        models.StudyPlan.student_id == req.student_id,
        models.StudyPlan.status == "active"
    ).update({"status": "archived"})
    db.commit()

    # Determine version
    max_version = db.query(models.StudyPlan).filter(
        models.StudyPlan.student_id == req.student_id
    ).count()

    # Create plan
    plan = models.StudyPlan(
        student_id=req.student_id,
        version=max_version + 1,
        status="active",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # Delete old scheduled sessions
    if req.force_regenerate:
        db.query(models.StudySession).filter(
            models.StudySession.student_id == req.student_id,
            models.StudySession.status == "scheduled",
        ).delete()
        db.commit()

    # Create new sessions
    created_sessions = []
    order = 0
    feasibility = None

    for s_dict in session_dicts:
        if "_feasibility" in s_dict:
            feasibility = s_dict.pop("_feasibility")

        # Remove internal keys
        clean = {k: v for k, v in s_dict.items() if not k.startswith("_")}
        # Parse ISO date string back to datetime
        if isinstance(clean.get("scheduled_start"), str):
            try:
                clean["scheduled_start"] = datetime.fromisoformat(clean["scheduled_start"])
            except ValueError:
                clean["scheduled_start"] = None

        session = models.StudySession(**clean)
        db.add(session)
        db.flush()

        plan_item = models.StudyPlanItem(
            plan_id=plan.id,
            session_id=session.id,
            order_index=order,
        )
        db.add(plan_item)
        order += 1
        created_sessions.append(session)

    db.commit()

    crud.log_activity(
        db, req.student_id, "plan_generated",
        f"Study plan v{plan.version} generated with {len(created_sessions)} sessions."
    )

    return {
        "plan_id": plan.id,
        "version": plan.version,
        "sessions_created": len(created_sessions),
        "feasibility": feasibility,
        "message": f"Study plan generated with {len(created_sessions)} sessions.",
    }


@router.get("/api/plans/current")
def get_current_plan(student_id: int = 1, db: Session = Depends(get_db)):
    """Get the active study plan."""
    _get_student_or_404(db, student_id)
    plan = crud.get_active_plan(db, student_id)
    if not plan:
        return {"plan": None, "sessions": [], "message": "No active plan. Generate one first."}

    sessions = crud.get_study_sessions_by_student(db, student_id)
    # Only return sessions in the current plan
    plan_session_ids = {item.session_id for item in plan.items if item.session_id}
    plan_sessions = [s for s in sessions if s.id in plan_session_ids]

    return {
        "plan": {
            "id": plan.id,
            "version": plan.version,
            "status": plan.status,
            "created_at": plan.created_at.isoformat(),
            "item_count": len(plan.items),
        },
        "sessions": [
            {
                "id": s.id,
                "topic_id": s.topic_id,
                "scheduled_start": s.scheduled_start.isoformat() if s.scheduled_start else None,
                "planned_minutes": s.planned_minutes,
                "actual_minutes": s.actual_minutes,
                "status": s.status,
                "notes": s.notes,
            }
            for s in plan_sessions
        ],
    }


@router.get("/api/plans/history")
def get_plan_history(student_id: int = 1, db: Session = Depends(get_db)):
    """Get all historical plans for a student."""
    _get_student_or_404(db, student_id)
    plans = crud.get_plan_history(db, student_id)
    return [
        {
            "id": p.id,
            "version": p.version,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
            "revision_reason": p.revision_reason,
            "item_count": len(p.items),
        }
        for p in plans
    ]


@router.post("/api/plans/replan")
def replan(req: schemas.ReplanRequest, db: Session = Depends(get_db)):
    """Trigger adaptive replanning."""
    _get_student_or_404(db, req.student_id)

    # Update plan with revision reason
    old_plan = crud.get_active_plan(db, req.student_id)
    if old_plan:
        old_plan.revision_reason = req.reason
        db.commit()

    # Delegate to generate_plan logic
    gen_req = schemas.PlanGenerateRequest(student_id=req.student_id, force_regenerate=True)
    return generate_plan(gen_req, db)


# ---------------------------------------------------------------------------
# Study Sessions
# ---------------------------------------------------------------------------
@router.get("/api/study-sessions")
def list_study_sessions(student_id: int = 1, db: Session = Depends(get_db)):
    """List all study sessions for a student."""
    _get_student_or_404(db, student_id)
    sessions = crud.get_study_sessions_by_student(db, student_id)
    return [
        {
            "id": s.id,
            "topic_id": s.topic_id,
            "scheduled_start": s.scheduled_start.isoformat() if s.scheduled_start else None,
            "planned_minutes": s.planned_minutes,
            "actual_minutes": s.actual_minutes,
            "status": s.status,
            "self_reported_understanding": s.self_reported_understanding,
            "notes": s.notes,
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ]


@router.patch("/api/study-sessions/{session_id}", response_model=schemas.StudySessionResponse)
def update_study_session(
    session_id: int,
    update: schemas.StudySessionUpdate,
    db: Session = Depends(get_db),
):
    """Update a study session (mark completed, log time, etc.)."""
    session = crud.update_study_session(db, session_id, update)
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")

    # If session completed, update topic mastery heuristically
    if update.status == "completed" and session.topic_id and update.self_reported_understanding:
        topic = crud.get_topic(db, session.topic_id)
        if topic:
            understanding = update.self_reported_understanding  # 1-5
            new_mastery = understanding / 5.0
            # Blend with existing mastery
            if topic.mastery_estimate is not None:
                blended = (topic.mastery_estimate * 0.6) + (new_mastery * 0.4)
            else:
                blended = new_mastery
            update_data = schemas.TopicUpdate(
                mastery_estimate=round(blended, 4),
                last_studied_at=datetime.utcnow(),
                status="in_progress" if blended < 0.9 else "completed",
            )
            crud.update_topic(db, session.topic_id, update_data)

    crud.log_activity(
        db, session.student_id, "session_updated",
        f"Session {session_id} marked as {update.status}."
    )
    return session
