"""
Constraint-aware study schedule generator for ExamWise AI.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .priority import calculate_priority_score


def _minutes_to_str(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m" if h else f"{m}m"


def generate_schedule(
    student_id: int,
    subjects: List[Dict[str, Any]],
    topics: List[Dict[str, Any]],
    preferences: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Constraint-aware scheduler.

    Constraints:
    - No overlapping sessions
    - Respect daily hour limits (from preferences)
    - Prioritize high-priority topics
    - Reserve 20% of daily time for revision
    - Validate feasibility and warn if overloaded
    - Return list of StudySession dicts (not yet saved to DB)

    Args:
        student_id: int
        subjects: list of subject dicts with exam_date, id
        topics: list of topic dicts with unit_id, estimated_minutes, mastery, etc.
        preferences: dict with:
            - daily_hours (float): max study hours per day
            - preferred_study_time (str): morning/afternoon/evening/night
            - start_date (datetime): when to start scheduling (default: today)

    Returns:
        List of session dicts ready to be inserted as StudySession rows.
    """
    daily_hours: float = float(preferences.get("daily_hours") or preferences.get("preferred_study_hours") or 4.0)
    daily_minutes: int = int(daily_hours * 60)
    revision_reserve: int = int(daily_minutes * 0.20)  # 20% reserved for revision
    study_minutes_per_day: int = daily_minutes - revision_reserve

    preferred_time: str = preferences.get("preferred_study_time") or "morning"
    start_date: datetime = preferences.get("start_date") or datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Determine session start hour based on preference
    time_hour_map = {
        "morning": 8,
        "afternoon": 13,
        "evening": 18,
        "night": 20,
    }
    start_hour = time_hour_map.get(preferred_time, 8)

    # Build subject exam date lookup
    subject_exam_map: Dict[int, Optional[datetime]] = {
        s["id"]: s.get("exam_date") for s in subjects
    }

    # Score and rank all topics
    scored_topics = []
    for topic in topics:
        subject_id = topic.get("subject_id")
        exam_date = subject_exam_map.get(subject_id) if subject_id else None
        topic_data = {
            "mastery_estimate": topic.get("mastery_estimate"),
            "exam_importance": topic.get("exam_importance"),
            "difficulty": topic.get("difficulty"),
            "exam_date": exam_date,
            "last_studied_at": topic.get("last_studied_at"),
            "status": topic.get("status"),
        }
        result = calculate_priority_score(topic_data)
        scored_topics.append({
            **topic,
            "priority_score": result["score"],
            "priority_explanation": result["explanation"],
            "_exam_date": exam_date,
        })

    # Sort by priority descending
    scored_topics.sort(key=lambda t: t["priority_score"], reverse=True)

    # Schedule sessions day by day
    sessions: List[Dict[str, Any]] = []
    current_date = start_date
    topic_queue = list(scored_topics)
    max_days = 90  # Don't schedule beyond 90 days
    days_used = 0

    while topic_queue and days_used < max_days:
        day_remaining = study_minutes_per_day
        session_start = current_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)

        # Skip if this day is past the earliest exam
        earliest_exam = None
        for subj in subjects:
            ed = subj.get("exam_date")
            if ed and (earliest_exam is None or ed < earliest_exam):
                earliest_exam = ed

        # Filter topics whose exam hasn't passed
        day_topics = [
            t for t in topic_queue
            if (t.get("_exam_date") is None or t["_exam_date"] >= current_date)
        ]

        if not day_topics:
            current_date += timedelta(days=1)
            days_used += 1
            continue

        scheduled_this_day = []
        for topic in list(day_topics):
            if day_remaining <= 0:
                break

            est = int(topic.get("estimated_minutes") or 60)
            # Cap single session at 90 minutes for cognitive load
            session_len = min(est, 90)
            session_len = min(session_len, day_remaining)

            if session_len < 15:
                # Not enough time for a meaningful session
                continue

            session = {
                "student_id": student_id,
                "topic_id": topic.get("id"),
                "scheduled_start": session_start.isoformat(),
                "planned_minutes": session_len,
                "actual_minutes": None,
                "status": "scheduled",
                "notes": f"Priority: {topic['priority_score']:.2f}. {topic.get('priority_explanation', '')}",
                "_topic_title": topic.get("title", ""),
                "_subject_id": topic.get("subject_id"),
                "_priority_score": topic["priority_score"],
            }
            sessions.append(session)
            scheduled_this_day.append(topic)

            # Advance session start time
            session_start = session_start + timedelta(minutes=session_len + 10)  # 10 min break
            day_remaining -= session_len

        # Remove scheduled topics from queue (only fully scheduled ones)
        for t in scheduled_this_day:
            if t in topic_queue:
                topic_queue.remove(t)

        # Add revision session if we have completed topics
        completed_topics = [
            t for t in scored_topics
            if t.get("status") == "completed" and t not in topic_queue
        ]
        if completed_topics and revision_reserve > 0:
            rev_topic = completed_topics[0]
            sessions.append({
                "student_id": student_id,
                "topic_id": rev_topic.get("id"),
                "scheduled_start": session_start.isoformat(),
                "planned_minutes": revision_reserve,
                "actual_minutes": None,
                "status": "scheduled",
                "notes": "Revision session",
                "_topic_title": rev_topic.get("title", ""),
                "_subject_id": rev_topic.get("subject_id"),
                "_priority_score": 0.0,
            })

        current_date += timedelta(days=1)
        days_used += 1

    # Feasibility check
    total_study_minutes = sum(s["planned_minutes"] for s in sessions)
    total_topic_minutes = sum(int(t.get("estimated_minutes") or 60) for t in scored_topics)

    feasibility = {
        "feasible": total_study_minutes >= total_topic_minutes * 0.6,
        "total_sessions": len(sessions),
        "days_planned": days_used,
        "scheduled_minutes": total_study_minutes,
        "required_minutes": total_topic_minutes,
        "unscheduled_topics": len(topic_queue),
    }

    # Embed feasibility info into first session note
    if sessions:
        sessions[0]["_feasibility"] = feasibility

    return sessions


def validate_schedule_feasibility(sessions: List[Dict], topics: List[Dict]) -> Dict:
    """Quick feasibility check without generating a full schedule."""
    total_scheduled = sum(s.get("planned_minutes", 0) for s in sessions)
    total_required = sum(int(t.get("estimated_minutes") or 60) for t in topics)
    coverage = total_scheduled / total_required if total_required > 0 else 0.0
    return {
        "feasible": coverage >= 0.6,
        "coverage_percent": round(coverage * 100, 1),
        "total_scheduled_hours": round(total_scheduled / 60, 1),
        "total_required_hours": round(total_required / 60, 1),
    }
