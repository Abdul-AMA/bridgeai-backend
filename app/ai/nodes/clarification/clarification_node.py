"""
Clarification Node using Anthropic LLM for requirement ambiguity detection.
Integrates memory search to provide context from previous interactions.
"""

from typing import Any, Dict

from app.ai.nodes.clarification.llm_ambiguity_detector import LLMAmbiguityDetector
from app.ai.state import AgentState


def clarification_node(state: AgentState) -> Dict[str, Any]:
    user_input = state.get("user_input", "")
    conversation_history = state.get("conversation_history", [])
    extracted_fields = state.get("extracted_fields", {})
    project_id = state.get("project_id")
    db = state.get("db")  # Optional: database session for memory lookup

    # Build context payload
    context = {
        "conversation_history": conversation_history,
        "extracted_fields": extracted_fields,
    }

    # Enrich context with relevant memories if available
    if db and project_id:
        try:
            from app.ai.memory_service import search_project_memories

            relevant_memories = search_project_memories(
                db=db,
                project_id=project_id,
                query=user_input,
                limit=3,
                similarity_threshold=0.2,
            )
            context["relevant_memories"] = [
                {
                    "text": m["text"],
                    "source_type": m["source_type"],
                    "similarity": m["similarity_score"],
                }
                for m in relevant_memories
            ]
        except Exception:
            context["relevant_memories"] = []

        # Enrich context with uploaded document chunks (RAG)
        try:
            from app.ai.memory_service import search_project_memories

            doc_results = search_project_memories(
                db=db,
                project_id=project_id,
                query=user_input,
                limit=3,
                similarity_threshold=0.25,
                source_type="document",
            )
            context["document_context"] = [
                {
                    "text": r["text"],
                    "filename": r.get("metadata", {}).get("filename", "uploaded document"),
                    "similarity": r["similarity_score"],
                }
                for r in doc_results
            ]
        except Exception:
            context["document_context"] = []

        # Fetch project context summary for prompt injection
        try:
            from app.services.summary_service import get_summary_content
            context["project_summary"] = get_summary_content(project_id, db)
        except Exception:
            context["project_summary"] = "No project summary available yet."

    # Run ambiguity detection
    detector = LLMAmbiguityDetector()
    result = detector.analyze_and_generate_questions(user_input, context)

    # Persist token usage (best-effort; never raises)
    usage_records = detector.get_usage_records()
    if usage_records and db and state.get("user_id"):
        try:
            from app.services.usage_service import log_usage_records
            log_usage_records(
                db,
                usage_records,
                user_id=state["user_id"],
                project_id=state.get("project_id"),
            )
        except Exception:
            pass

    ambiguities = result["ambiguities"]
    clarification_questions = result["clarification_questions"]
    clarity_score = result["clarity_score"]
    summary = result["summary"]
    needs_clarification = result["needs_clarification"]

    intent = result.get("intent", "requirement")

    # Build response message
    if needs_clarification:
        response = "I'd like to clarify a few points:\n\n"
        for i, q in enumerate(clarification_questions, 1):
            response += f"{i}. {q}\n"
    elif intent == "greeting":
        response = "Hello! How can I help you with your project requirements today?"
    elif intent == "question":
        response = "I am a Business Analyst AI assistant. I can help you define and clarify your project requirements. Please describe what you'd like to build."
    elif intent == "deferral":
        response = "Understood. We will skip those details for now."
    else:
        # Default for clear requirements
        response = f"Your requirements are clear. (Clarity Score: {clarity_score}/100)"

    return {
        "clarification_questions": clarification_questions,
        "ambiguities": [
            {
                "type": a.type,
                "field": a.field,
                "reason": a.reason,
                "severity": a.severity,
                "suggestion": a.suggestion,
            }
            for a in ambiguities
        ],
        "needs_clarification": needs_clarification,
        "clarity_score": clarity_score,
        "quality_summary": summary,
        "output": response,
        "last_node": "clarification",
        "intent": intent,
        "document_context": context.get("document_context", []),
        "project_summary": context.get("project_summary", "No project summary available yet."),
    }


def should_request_clarification(state: AgentState) -> bool:
    """
    Determine if the workflow should stop after clarification.
    Returns True (stop) if:
    1. Clarification is needed (ambiguities found)
    2. Intent is NOT a requirement (greeting, question, deferral)
    """
    needs_clarification = state.get("needs_clarification", False)
    intent = state.get("intent", "requirement")

    # If it's a greeting/question/deferral, we stop here and return the response
    if intent != "requirement":
        return True

    # If it's a requirement but needs clarification, we also stop
    return needs_clarification
