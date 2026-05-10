"""
RTM Extraction Service — extracts discrete requirements from a CRS document.

Hybrid strategy:
- Section value is a list  → one requirement per list item (no LLM needed)
- Section value is a string → LLM call to extract discrete requirement statements as JSON array
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.json_utils import safe_json_loads

logger = logging.getLogger(__name__)

NARRATIVE_EXTRACTION_PROMPT = """\
You are a requirements analyst. The following is a section of a requirements document.
Extract every distinct requirement statement as a JSON array of strings.
Each string must be one complete, self-contained requirement.
Return ONLY the JSON array — no markdown, no explanation.

Section content:
{content}
"""


@dataclass
class RequirementData:
    section: str
    full_text: str
    description: str
    req_id: str = ""


def _next_req_number(project_id: int, db: Session) -> int:
    from app.models.requirement import Requirement
    from sqlalchemy import func

    result = (
        db.query(func.max(Requirement.req_id))
        .filter(Requirement.project_id == project_id)
        .scalar()
    )
    if result is None:
        return 1
    try:
        return int(result.split("-")[1]) + 1
    except (IndexError, ValueError):
        return 1


def _extract_from_narrative(section: str, content: str) -> list[str]:
    from app.ai.llm_factory import LLMFactory

    llm = LLMFactory.create_clarification_llm()
    prompt = NARRATIVE_EXTRACTION_PROMPT.format(content=content)
    try:
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        statements = safe_json_loads(text, default=[])
        if isinstance(statements, list):
            return [s for s in statements if isinstance(s, str) and s.strip()]
    except Exception as exc:
        logger.error(f"LLM extraction failed for section '{section}': {exc}")
    return []


def extract_requirements(crs_document: Any, db: Session) -> list[RequirementData]:
    """
    Parse a CRS document and return a flat list of RequirementData.

    crs_document must have:
      - .id (int)
      - .project_id (int)
      - .content (str) — JSON string mapping section names to values
    """
    content_map: dict = safe_json_loads(crs_document.content, default={})
    if not isinstance(content_map, dict):
        logger.warning(
            f"CRS {crs_document.id} content is not a JSON object — skipping extraction"
        )
        return []

    counter = _next_req_number(crs_document.project_id, db)
    results: list[RequirementData] = []

    for section, value in content_map.items():
        statements: list[str] = []

        if isinstance(value, list):
            statements = [str(item).strip() for item in value if str(item).strip()]
        elif isinstance(value, str) and value.strip():
            statements = _extract_from_narrative(section, value)
        elif isinstance(value, dict):
            # Nested sub-sections — recurse one level
            for sub_section, sub_value in value.items():
                full_section = f"{section}.{sub_section}"
                if isinstance(sub_value, list):
                    sub_statements = [str(i).strip() for i in sub_value if str(i).strip()]
                elif isinstance(sub_value, str) and sub_value.strip():
                    sub_statements = _extract_from_narrative(full_section, sub_value)
                else:
                    continue
                for stmt in sub_statements:
                    req_id = f"REQ-{counter:03d}"
                    results.append(
                        RequirementData(
                            section=full_section,
                            full_text=stmt,
                            description=stmt[:100] if len(stmt) > 100 else stmt,
                            req_id=req_id,
                        )
                    )
                    counter += 1
            continue

        for stmt in statements:
            req_id = f"REQ-{counter:03d}"
            results.append(
                RequirementData(
                    section=section,
                    full_text=stmt,
                    description=stmt[:100] if len(stmt) > 100 else stmt,
                    req_id=req_id,
                )
            )
            counter += 1

    logger.info(
        f"Extracted {len(results)} requirements from CRS {crs_document.id}"
    )
    return results
