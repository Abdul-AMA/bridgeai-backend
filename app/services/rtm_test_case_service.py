"""
RTM Test Case Service — AI batch generation of test cases for requirements.

Batches up to 10 requirements per LLM call. Prompt requests a JSON array of
test case objects keyed by requirement ID.
"""

import json
import logging

from sqlalchemy.orm import Session

from app.core.json_utils import safe_json_loads

logger = logging.getLogger(__name__)

BATCH_SIZE = 10

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


def generate_test_cases(requirement_ids: list[int], db: Session) -> list:
    """
    AI-generate test cases for the given requirement IDs.
    Processes in batches of up to BATCH_SIZE per LLM call.
    Returns the list of persisted TestCase ORM objects.
    """
    from app.models.requirement import Requirement
    from app.models.test_case import TestCase
    from app.ai.llm_factory import LLMFactory

    requirements = (
        db.query(Requirement)
        .filter(Requirement.id.in_(requirement_ids))
        .all()
    )
    if not requirements:
        return []

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
                steps = item.get("steps", [])
                tc = TestCase(
                    requirement_id=int(req_id),
                    title=str(item.get("title", ""))[:300],
                    preconditions=item.get("preconditions") or None,
                    steps=json.dumps(steps) if isinstance(steps, list) else str(steps),
                    expected_result=str(item.get("expected_result", "")),
                    is_auto_generated=True,
                )
                db.add(tc)
                created.append(tc)

        except Exception as exc:
            logger.error(f"Test case generation failed for batch: {exc}", exc_info=True)

    if created:
        db.flush()

    logger.info(f"Generated {len(created)} test cases for {len(requirements)} requirements")
    return created
