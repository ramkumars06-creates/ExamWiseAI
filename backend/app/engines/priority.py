"""
Priority Scoring Engine for ExamWise AI

Weighted formula:
  Priority = 0.30 * knowledge_gap
           + 0.25 * exam_importance
           + 0.15 * difficulty
           + 0.20 * deadline_urgency
           + 0.10 * revision_need

All components normalized to [0, 1].
Weights are configurable defaults, not empirically optimized values.
"""
from datetime import datetime, timezone
from typing import Optional
import math


# Default weights (configurable via settings)
DEFAULT_WEIGHTS = {
    "knowledge_gap": 0.30,
    "exam_importance": 0.25,
    "difficulty": 0.15,
    "deadline_urgency": 0.20,
    "revision_need": 0.10,
}

# Default exam importance when not specified
DEFAULT_EXAM_IMPORTANCE = 0.5

# Days beyond which deadline urgency plateaus (low urgency)
URGENCY_PLATEAU_DAYS = 60


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, value))


def calculate_knowledge_gap(mastery_estimate: Optional[float]) -> float:
    """
    Knowledge gap = 1 - mastery.
    Unassessed topics (mastery=None) get a conservative gap of 0.7
    (they are likely not mastered, but we acknowledge uncertainty).
    """
    if mastery_estimate is None:
        return 0.7  # Conservative: unassessed is not mastered
    return _clamp(1.0 - mastery_estimate)


def calculate_deadline_urgency(exam_date: Optional[datetime]) -> tuple[float, str]:
    """
    Deadline urgency increases as exam approaches.
    Uses a logistic-like curve:
      urgency = 1 / (1 + exp(0.1 * (days - 15)))
    
    At 0 days: urgency ≈ 1.0
    At 15 days: urgency = 0.5
    At 60 days: urgency ≈ 0.05
    
    Returns (urgency_score, explanation).
    """
    if exam_date is None:
        return 0.5, "No exam date set; using default urgency."

    now = datetime.now(timezone.utc)
    # Make exam_date timezone-aware if needed
    if exam_date.tzinfo is None:
        exam_date = exam_date.replace(tzinfo=timezone.utc)

    days_remaining = (exam_date - now).total_seconds() / 86400

    if days_remaining < 0:
        return 1.0, f"Exam has passed ({abs(int(days_remaining))} days ago)."

    if days_remaining == 0:
        return 1.0, "Exam is today!"

    # Logistic urgency: peaks near 0 days, low at 60+ days
    k = 0.15  # steepness
    midpoint = 14  # 50% urgency at 14 days remaining
    urgency = 1.0 / (1.0 + math.exp(k * (days_remaining - midpoint)))
    urgency = _clamp(urgency)

    days_int = int(days_remaining)
    if days_int <= 7:
        label = f"{days_int} days remaining — critical urgency."
    elif days_int <= 21:
        label = f"{days_int} days remaining — high urgency."
    elif days_int <= 45:
        label = f"{days_int} days remaining — moderate urgency."
    else:
        label = f"{days_int} days remaining — low urgency."

    return urgency, label


def calculate_revision_need(
    last_studied_at: Optional[datetime],
    mastery_estimate: Optional[float],
) -> tuple[float, str]:
    """
    Revision need considers:
    - Time since last review (forgetting curve approximation)
    - Previous mastery (higher mastery = less urgent revision, but still needed)

    Forgetting curve: memory decays with time since last study.
    Need = time_decay * (0.6 + 0.4 * mastery)

    Returns (need_score, explanation).
    """
    if last_studied_at is None:
        return 0.5, "Never studied; revision need is moderate by default."

    now = datetime.now(timezone.utc)
    if last_studied_at.tzinfo is None:
        last_studied_at = last_studied_at.replace(tzinfo=timezone.utc)

    days_since = (now - last_studied_at).total_seconds() / 86400

    # Forgetting curve: ~50% retention after 7 days for average material
    # time_decay = 1 - exp(-days / half_life)
    half_life = 7.0  # days
    time_decay = 1.0 - math.exp(-days_since / half_life)
    time_decay = _clamp(time_decay)

    # If mastery is unknown, treat as moderate
    mastery = mastery_estimate if mastery_estimate is not None else 0.5
    # High mastery topics still need revision, but less urgently
    revision_need = time_decay * (0.5 + 0.5 * (1.0 - mastery))
    revision_need = _clamp(revision_need)

    days_int = int(days_since)
    return revision_need, f"Last studied {days_int} days ago."


def calculate_priority_score(
    topic_data: dict,
    weights: Optional[dict] = None,
    exam_date: Optional[datetime] = None,
) -> dict:
    """
    Calculate a normalized topic priority score with full explanation.

    Input dict keys (all optional with safe defaults):
    - mastery_estimate: float|None (0-1)
    - exam_importance: float (0-1)
    - difficulty: float (0-1)
    - last_studied_at: datetime|None
    - estimated_minutes: int

    Returns:
    - priority_score: float (0-1)
    - components: dict with per-component scores
    - explanation: str
    - weights_used: dict
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}

    # Validate weights sum to ~1
    weight_sum = sum(w.values())
    if abs(weight_sum - 1.0) > 0.05:
        # Normalize weights to sum to 1
        w = {k: v / weight_sum for k, v in w.items()}

    # Extract topic fields
    mastery = topic_data.get("mastery_estimate")
    importance = topic_data.get("exam_importance")
    difficulty = topic_data.get("difficulty", 0.5)
    last_studied = topic_data.get("last_studied_at")

    # Handle missing exam importance
    if importance is None:
        importance = DEFAULT_EXAM_IMPORTANCE
        importance_note = f"Exam importance not set; using default {DEFAULT_EXAM_IMPORTANCE}."
    else:
        importance = _clamp(float(importance))
        importance_note = f"Exam importance: {importance:.0%}."

    # Calculate components
    knowledge_gap = calculate_knowledge_gap(mastery)

    urgency, urgency_note = calculate_deadline_urgency(exam_date)

    revision_need, revision_note = calculate_revision_need(last_studied, mastery)

    difficulty_score = _clamp(float(difficulty))

    # Weighted sum
    score = (
        w["knowledge_gap"] * knowledge_gap
        + w["exam_importance"] * importance
        + w["difficulty"] * difficulty_score
        + w["deadline_urgency"] * urgency
        + w["revision_need"] * revision_need
    )
    score = _clamp(score)

    # Build explanation
    mastery_pct = f"{mastery:.0%}" if mastery is not None else "unassessed"
    explanation_parts = [
        f"Knowledge gap: {knowledge_gap:.0%} (mastery: {mastery_pct}).",
        importance_note,
        f"Difficulty: {difficulty_score:.0%}.",
        urgency_note,
        revision_note,
    ]
    explanation = " ".join(explanation_parts)

    return {
        "priority_score": round(score, 4),
        "components": {
            "knowledge_gap": round(knowledge_gap, 4),
            "exam_importance": round(importance, 4),
            "difficulty": round(difficulty_score, 4),
            "deadline_urgency": round(urgency, 4),
            "revision_need": round(revision_need, 4),
        },
        "explanation": explanation,
        "weights_used": {k: round(v, 3) for k, v in w.items()},
    }


def rank_topics(topics: list, exam_date: Optional[datetime] = None, weights: Optional[dict] = None) -> list:
    """
    Rank a list of topic dicts by priority score.
    Each dict should have: mastery_estimate, exam_importance, difficulty,
                           last_studied_at, estimated_minutes, title.
    Returns list sorted descending by priority_score.
    """
    scored = []
    for t in topics:
        result = calculate_priority_score(t, weights=weights, exam_date=exam_date)
        scored.append({**t, **result})
    return sorted(scored, key=lambda x: x["priority_score"], reverse=True)
