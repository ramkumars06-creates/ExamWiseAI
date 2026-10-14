"""
Exam readiness calculator for ExamWise AI.
Combines syllabus coverage, topic mastery, and assessment performance.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .. import models


def _safe_avg(values: list) -> Optional[float]:
    """Return mean of a list, or None if empty."""
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return sum(clean) / len(clean)


def _mastery_to_float(mastery: Optional[float]) -> Optional[float]:
    if mastery is None:
        return None
    return max(0.0, min(1.0, mastery))


def calculate_readiness(subject_id: int, db: Session) -> dict:
    """
    Calculate exam readiness for a given subject.

    Returns:
        {
            "syllabus_coverage": float (0-1),
            "topic_mastery": float (0-1) or None,
            "assessment_performance": float (0-1) or None,
            "overall_readiness": float (0-1) or None,
            "confidence_level": "low" | "medium" | "high",
            "recommendation": str,
            "insufficient_data": bool,
            "topic_breakdown": list[dict],
        }
    """
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        return {
            "syllabus_coverage": 0.0,
            "topic_mastery": None,
            "assessment_performance": None,
            "overall_readiness": None,
            "confidence_level": "low",
            "recommendation": "Subject not found.",
            "insufficient_data": True,
            "topic_breakdown": [],
        }

    # --- Collect all topics for the subject ---
    units = db.query(models.Unit).filter(models.Unit.subject_id == subject_id).all()
    all_topics: list[models.Topic] = []
    for unit in units:
        topics = db.query(models.Topic).filter(models.Topic.unit_id == unit.id).all()
        all_topics.extend(topics)

    total_topics = len(all_topics)

    if total_topics == 0:
        return {
            "syllabus_coverage": 0.0,
            "topic_mastery": None,
            "assessment_performance": None,
            "overall_readiness": None,
            "confidence_level": "low",
            "recommendation": "No topics defined. Upload syllabus or add topics to begin.",
            "insufficient_data": True,
            "topic_breakdown": [],
        }

    # --- Syllabus Coverage ---
    # Count topics that are not "not_started" or have been studied at least once
    covered = [
        t for t in all_topics
        if t.status in ("in_progress", "completed") or t.last_studied_at is not None
    ]
    syllabus_coverage = len(covered) / total_topics

    # --- Topic Mastery ---
    mastery_values = [_mastery_to_float(t.mastery_estimate) for t in all_topics if t.mastery_estimate is not None]
    topic_mastery = _safe_avg(mastery_values)

    # --- Assessment Performance ---
    assessments = (
        db.query(models.Assessment)
        .filter(
            models.Assessment.subject_id == subject_id,
            models.Assessment.score.isnot(None),
            models.Assessment.total_questions > 0,
        )
        .all()
    )
    if assessments:
        perf_values = [
            (a.score / a.total_questions) for a in assessments
            if a.total_questions and a.score is not None
        ]
        assessment_performance = _safe_avg(perf_values)
    else:
        assessment_performance = None

    # --- Overall Readiness ---
    insufficient_data = topic_mastery is None and assessment_performance is None

    if not insufficient_data:
        weights = []
        weighted_sum = 0.0

        # Syllabus coverage always counted (weight 0.25)
        weighted_sum += 0.25 * syllabus_coverage
        weights.append(0.25)

        if topic_mastery is not None:
            weighted_sum += 0.45 * topic_mastery
            weights.append(0.45)

        if assessment_performance is not None:
            ap_weight = 0.30 if topic_mastery is not None else 0.75
            weighted_sum += ap_weight * assessment_performance
            weights.append(ap_weight)

        total_weight = sum(weights)
        overall_readiness = weighted_sum / total_weight if total_weight > 0 else None
        if overall_readiness is not None:
            overall_readiness = round(overall_readiness, 4)
    else:
        overall_readiness = None

    # --- Confidence Level ---
    if overall_readiness is None:
        confidence_level = "low"
    elif overall_readiness >= 0.75:
        confidence_level = "high"
    elif overall_readiness >= 0.50:
        confidence_level = "medium"
    else:
        confidence_level = "low"

    # --- Recommendation ---
    recommendations = []
    if syllabus_coverage < 0.5:
        recommendations.append("Cover more topics — less than half the syllabus has been started.")
    if topic_mastery is not None and topic_mastery < 0.5:
        recommendations.append("Focus on improving mastery for weak topics.")
    if assessment_performance is not None and assessment_performance < 0.6:
        recommendations.append("Practice more assessments to strengthen recall.")
    if not assessments:
        recommendations.append("Take at least one practice assessment to gauge readiness.")

    if not recommendations:
        if overall_readiness and overall_readiness >= 0.75:
            recommendations.append("Great progress! Keep up regular revision.")
        else:
            recommendations.append("Continue studying systematically to build readiness.")

    recommendation = " ".join(recommendations)

    # --- Topic Breakdown ---
    topic_breakdown = []
    for t in all_topics:
        topic_breakdown.append({
            "topic_id": t.id,
            "title": t.title,
            "status": t.status,
            "mastery_estimate": t.mastery_estimate,
            "difficulty": t.difficulty,
            "exam_importance": t.exam_importance,
        })

    return {
        "syllabus_coverage": round(syllabus_coverage, 4),
        "topic_mastery": round(topic_mastery, 4) if topic_mastery is not None else None,
        "assessment_performance": round(assessment_performance, 4) if assessment_performance is not None else None,
        "overall_readiness": overall_readiness,
        "confidence_level": confidence_level,
        "recommendation": recommendation,
        "insufficient_data": insufficient_data,
        "topic_breakdown": topic_breakdown,
        "total_topics": total_topics,
        "covered_topics": len(covered),
    }
