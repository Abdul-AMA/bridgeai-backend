"""
AI usage tracking service — persists token usage logs and provides aggregated statistics.
Cost estimation is approximate and covers the main providers supported by the platform.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.ai_usage_log import AIUsageLog

logger = logging.getLogger(__name__)

# Approximate pricing per 1M tokens (USD) keyed by substring of model name.
# Checked against public pricing pages; update as providers change rates.
_COST_PER_1M: List[tuple] = [
    # Anthropic
    ("claude-opus",       3.00,   15.00),   # Opus 3 / Opus 4
    ("claude-sonnet",     3.00,   15.00),   # Sonnet 3.5 / 4.x
    ("claude-haiku",      0.25,    1.25),   # Haiku 3 / 4
    ("claude",            3.00,   15.00),   # generic Claude fallback
    # OpenAI
    ("gpt-4o-mini",       0.15,    0.60),
    ("gpt-4o",            5.00,   15.00),
    ("gpt-4-turbo",      10.00,   30.00),
    ("gpt-4",            30.00,   60.00),
    ("gpt-3.5",           0.50,    1.50),
    ("o1-mini",           3.00,   12.00),
    ("o1",               15.00,   60.00),
    # Google Gemini
    ("gemini-1.5-pro",    3.50,   10.50),
    ("gemini-1.5-flash",  0.075,   0.30),
    ("gemini-1.0-pro",    0.50,    1.50),
    # Groq inference (paid tier rates; free-quota usage accrues $0 actual cost)
    ("llama-3.3-70b",     0.59,    0.79),   # llama-3.3-70b-versatile
    ("llama-3.1-70b",     0.59,    0.79),   # llama-3.1-70b-versatile
    ("llama-3.1-8b",      0.05,    0.08),   # llama-3.1-8b-instant
    ("llama3-70b",        0.59,    0.79),   # llama3-70b-8192
    ("llama3-8b",         0.05,    0.08),   # llama3-8b-8192
    ("mixtral",           0.27,    0.27),
    # Mistral
    ("mistral-large",     8.00,   24.00),
    ("mistral-small",     2.00,    6.00),
    ("mistral-7b",        0.25,    0.25),
]
_DEFAULT_COST = (3.00, 15.00)


def _estimate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    model_lower = model_name.lower()
    for key, in_price, out_price in _COST_PER_1M:
        if key in model_lower:
            return (input_tokens / 1_000_000) * in_price + (output_tokens / 1_000_000) * out_price
    in_price, out_price = _DEFAULT_COST
    return (input_tokens / 1_000_000) * in_price + (output_tokens / 1_000_000) * out_price


def log_usage_records(
    db: Session,
    records: List[Dict[str, Any]],
    user_id: int,
    project_id: Optional[int] = None,
    session_id: Optional[int] = None,
) -> None:
    """Persist a batch of usage records collected from AI node calls."""
    if not records:
        return
    try:
        for rec in records:
            db.add(AIUsageLog(
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                node_type=rec.get("node_type", "unknown"),
                model_name=rec.get("model_name", "unknown"),
                provider=rec.get("provider", "unknown"),
                input_tokens=rec.get("input_tokens", 0),
                output_tokens=rec.get("output_tokens", 0),
                total_tokens=rec.get("total_tokens", 0),
            ))
        db.commit()
    except Exception as exc:
        logger.error(f"Failed to persist usage records: {exc}")
        db.rollback()


def get_user_summary(db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
    """Return aggregated usage statistics for a user over the last N days."""
    since = datetime.utcnow() - timedelta(days=days)
    logs: List[AIUsageLog] = (
        db.query(AIUsageLog)
        .filter(AIUsageLog.user_id == user_id, AIUsageLog.created_at >= since)
        .all()
    )

    total_input = sum(l.input_tokens for l in logs)
    total_output = sum(l.output_tokens for l in logs)
    total_tokens = sum(l.total_tokens for l in logs)
    estimated_cost = sum(
        _estimate_cost(l.model_name, l.input_tokens, l.output_tokens) for l in logs
    )

    by_node_type: Dict[str, Dict] = {}
    for log in logs:
        entry = by_node_type.setdefault(log.node_type, {"calls": 0, "tokens": 0})
        entry["calls"] += 1
        entry["tokens"] += log.total_tokens

    daily: Dict[str, Dict] = {}
    for log in logs:
        date_str = log.created_at.strftime("%Y-%m-%d")
        entry = daily.setdefault(date_str, {"calls": 0, "input_tokens": 0, "output_tokens": 0})
        entry["calls"] += 1
        entry["input_tokens"] += log.input_tokens
        entry["output_tokens"] += log.output_tokens

    return {
        "total_calls": len(logs),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_tokens,
        "by_node_type": by_node_type,
        "daily_breakdown": [{"date": k, **v} for k, v in sorted(daily.items())],
        "estimated_cost_usd": round(estimated_cost, 4),
    }


def get_user_history(
    db: Session, user_id: int, page: int = 1, limit: int = 20
) -> Dict[str, Any]:
    """Return a paginated list of usage log entries for a user."""
    offset = (page - 1) * limit
    total = db.query(AIUsageLog).filter(AIUsageLog.user_id == user_id).count()
    items = (
        db.query(AIUsageLog)
        .filter(AIUsageLog.user_id == user_id)
        .order_by(AIUsageLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "page": page, "limit": limit, "items": items}
