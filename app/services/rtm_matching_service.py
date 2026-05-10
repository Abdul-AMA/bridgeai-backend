"""
RTM Matching Service — matches new requirements against existing ones using semantic similarity.

On RTM refresh, new requirements are embedded and compared against all active requirements
for the project. Pairs above the 0.82 threshold are considered the same requirement:
  - Links and test cases are migrated from the old record to the new one
  - The old record is archived

New requirements with no match above threshold are inserted as fresh records.
Old records with no match are archived.
"""

import logging
from dataclasses import dataclass, field

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.services.rtm_extraction_service import RequirementData

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.82

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


@dataclass
class MatchResult:
    matched: list[tuple[RequirementData, int]] = field(default_factory=list)
    # (new_req_data, old_requirement_id)
    unmatched: list[RequirementData] = field(default_factory=list)
    removed_ids: list[int] = field(default_factory=list)


def match_requirements(
    new_reqs: list[RequirementData], project_id: int, db: Session
) -> MatchResult:
    """
    Match new requirements against active requirements in the project.

    Returns a MatchResult with:
      - matched: new requirements paired with their best existing requirement ID
      - unmatched: new requirements with no prior match (need insertion)
      - removed_ids: existing requirement IDs with no match in the new set (need archiving)
    """
    from app.models.requirement import Requirement, RequirementStatus

    existing = (
        db.query(Requirement)
        .filter(
            Requirement.project_id == project_id,
            Requirement.status == RequirementStatus.active,
        )
        .all()
    )

    if not existing:
        return MatchResult(unmatched=new_reqs)

    if not new_reqs:
        return MatchResult(removed_ids=[r.id for r in existing])

    model = _get_model()

    new_texts = [r.full_text for r in new_reqs]
    old_texts = [r.full_text for r in existing]

    new_embeddings = model.encode(new_texts, convert_to_numpy=True)
    old_embeddings = model.encode(old_texts, convert_to_numpy=True)

    result = MatchResult()
    matched_old_ids: set[int] = set()

    for i, new_req in enumerate(new_reqs):
        best_sim = -1.0
        best_old_idx = -1
        for j in range(len(existing)):
            sim = _cosine_similarity(new_embeddings[i], old_embeddings[j])
            if sim > best_sim:
                best_sim = sim
                best_old_idx = j

        if best_sim >= SIMILARITY_THRESHOLD:
            old_id = existing[best_old_idx].id
            result.matched.append((new_req, old_id))
            matched_old_ids.add(old_id)
            logger.debug(
                f"Matched new req '{new_req.req_id}' to existing {old_id} (sim={best_sim:.3f})"
            )
        else:
            result.unmatched.append(new_req)

    result.removed_ids = [r.id for r in existing if r.id not in matched_old_ids]

    logger.info(
        f"Match result for project {project_id}: "
        f"{len(result.matched)} matched, {len(result.unmatched)} new, "
        f"{len(result.removed_ids)} removed"
    )
    return result


def migrate_links_and_test_cases(
    old_requirement_id: int, new_requirement_id: int, db: Session
) -> None:
    """Copy manually-added links and all test cases from old requirement to new."""
    from app.models.traceability_link import TraceabilityLink
    from app.models.test_case import TestCase

    # Migrate manually-added links only (auto-generated will be re-created by source linker)
    manual_links = (
        db.query(TraceabilityLink)
        .filter(
            TraceabilityLink.requirement_id == old_requirement_id,
            TraceabilityLink.is_auto_generated.is_(False),
        )
        .all()
    )
    for link in manual_links:
        db.add(
            TraceabilityLink(
                requirement_id=new_requirement_id,
                source_type=link.source_type,
                source_id=link.source_id,
                excerpt=link.excerpt,
                is_auto_generated=False,
            )
        )

    # Migrate all test cases
    test_cases = (
        db.query(TestCase)
        .filter(TestCase.requirement_id == old_requirement_id)
        .all()
    )
    for tc in test_cases:
        db.add(
            TestCase(
                requirement_id=new_requirement_id,
                title=tc.title,
                preconditions=tc.preconditions,
                steps=tc.steps,
                expected_result=tc.expected_result,
                is_auto_generated=tc.is_auto_generated,
                status=tc.status,
            )
        )
