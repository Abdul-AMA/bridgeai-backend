"""
RTM Test Case Service — AI batch generation of test cases for requirements.

Batches up to 10 requirements per LLM call. Prompt requests a JSON array of
test case objects keyed by requirement ID.
"""

import json
import logging
from difflib import SequenceMatcher
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from app.core.json_utils import safe_json_loads

logger = logging.getLogger(__name__)

BATCH_SIZE = 10
FUZZY_THRESHOLD = 0.85
SEMANTIC_THRESHOLD = 0.85

TEST_CASE_PROMPT = """\
You are a QA engineer. For each requirement below, generate one or more test cases.
Return ONLY a JSON array (no markdown, no explanation) with this exact structure:
[
  {{
    "requirement_id": <int>,
    "title": "<short test case name>",
    "preconditions": "<state before the test, or null>",
    "steps": ["<step 1>", "<step 2>", ...],
    "expected_result": "<what a passing outcome looks like>"
  }},
  ...
]

Requirements:
{requirements_block}
"""


def _is_duplicate(
    new_title: str,
    existing: list[tuple[str, Optional[np.ndarray]]],
    model,
) -> bool:
    """
    Three-layer duplicate check (cheapest first):
    1. Exact lowercase match
    2. Fuzzy string ratio > FUZZY_THRESHOLD
    3. Semantic cosine similarity > SEMANTIC_THRESHOLD
    """
    norm_new = new_title.lower().strip()
    new_emb: Optional[np.ndarray] = None  # computed lazily, at most once

    for existing_norm, existing_emb in existing:
        # Layer 1: exact
        if norm_new == existing_norm:
            return True

        # Layer 2: fuzzy
        if SequenceMatcher(None, norm_new, existing_norm).ratio() > FUZZY_THRESHOLD:
            return True

        # Layer 3: semantic (only when embeddings are available)
        if existing_emb is not None:
            if new_emb is None:
                new_emb = model.encode([new_title], convert_to_numpy=True)[0]
            norm_a = np.linalg.norm(new_emb)
            norm_b = np.linalg.norm(existing_emb)
            if norm_a > 0 and norm_b > 0:
                sim = float(np.dot(new_emb, existing_emb) / (norm_a * norm_b))
                if sim > SEMANTIC_THRESHOLD:
                    return True

    return False


def generate_test_cases(requirement_ids: list[int], db: Session) -> list:
    """
    AI-generate test cases for the given requirement IDs.
    Processes in batches of up to BATCH_SIZE per LLM call.
    Skips titles that are exact, fuzzy, or semantically duplicate of existing ones.
    Returns the list of persisted TestCase ORM objects.
    """
    from app.models.requirement import Requirement
    from app.models.test_case import TestCase
    from app.ai.llm_factory import LLMFactory
    from app.services.rtm_matching_service import _get_model

    requirements = (
        db.query(Requirement)
        .filter(Requirement.id.in_(requirement_ids))
        .all()
    )
    if not requirements:
        return []

    # Load existing test case titles from DB
    existing_tcs = (
        db.query(TestCase.requirement_id, TestCase.title)
        .filter(TestCase.requirement_id.in_(requirement_ids))
        .all()
    )

    # Batch-embed all existing titles at once (single model call)
    model = _get_model()
    existing_data: dict[int, list[tuple[str, Optional[np.ndarray]]]] = {}

    if existing_tcs:
        texts = [title for _, title in existing_tcs]
        embeddings = model.encode(texts, convert_to_numpy=True)
        for (req_id, title), emb in zip(existing_tcs, embeddings):
            existing_data.setdefault(req_id, []).append((title.lower().strip(), emb))

    llm = LLMFactory.create_clarification_llm()
    created: list[TestCase] = []

    for batch_start in range(0, len(requirements), BATCH_SIZE):
        batch = requirements[batch_start: batch_start + BATCH_SIZE]
        req_block = "\n".join(
            f"ID {r.id}: {r.full_text}" for r in batch
        )
        prompt = TEST_CASE_PROMPT.format(requirements_block=req_block)

        try:
            response = llm.invoke(prompt)
            raw = response.content if hasattr(response, "content") else str(response)
            items = safe_json_loads(raw, default=[])
            if not isinstance(items, list):
                logger.warning(f"LLM returned non-list for test case batch: {raw[:200]}")
                continue

            for item in items:
                req_id = item.get("requirement_id")
                if req_id is None:
                    continue
                title = str(item.get("title", ""))[:300]
                existing = existing_data.get(int(req_id), [])

                if _is_duplicate(title, existing, model):
                    logger.debug(f"Skipping duplicate test case '{title}' for req {req_id}")
                    continue

                steps = item.get("steps", [])
                tc = TestCase(
                    requirement_id=int(req_id),
                    title=title,
                    preconditions=item.get("preconditions") or None,
                    steps=json.dumps(steps) if isinstance(steps, list) else str(steps),
                    expected_result=str(item.get("expected_result", "")),
                    is_auto_generated=True,
                )
                db.add(tc)
                # Add to existing_data with no embedding (exact match will catch it)
                existing_data.setdefault(int(req_id), []).append((title.lower().strip(), None))
                created.append(tc)

        except Exception as exc:
            logger.error(f"Test case generation failed for batch: {exc}", exc_info=True)

    if created:
        db.flush()

    logger.info(f"Generated {len(created)} test cases for {len(requirements)} requirements")
    return created
