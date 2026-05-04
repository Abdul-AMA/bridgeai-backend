"""
Template Filler Node for LangGraph workflow.
Maps clarified requirements to a structured CRS template.
"""

from typing import Any, Dict

from app.ai.nodes.template_filler.llm_template_filler import LLMTemplateFiller
from app.ai.state import AgentState
from app.services.crs_service import persist_crs_document


def template_filler_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node that fills a CRS template from clarified requirements.

    This node should be called after the clarification node has confirmed
    that requirements are clear (no more clarification needed).

    Args:
        state: The current AgentState containing user_input, conversation_history,
               and any previously extracted_fields

    Returns:
        Updated state with:
            - crs_content: JSON string of the filled CRS template
            - crs_template: Dictionary representation of the CRS
            - summary_points: List of key summary points
            - extracted_fields: Updated extracted fields from the template
            - output: Human-readable response
            - last_node: "template_filler"
    """
    user_input = state.get("user_input", "")
    conversation_history = state.get("conversation_history", [])
    extracted_fields = state.get("extracted_fields", {})
    db = state.get("db")
    project_id = state.get("project_id")
    user_id = state.get("user_id")
    crs_pattern = state.get("crs_pattern")

    # Retrieve relevant document chunks from project knowledge base
    document_context = []
    if db and project_id:
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
            document_context = doc_results
        except Exception:
            pass

    # Fetch project context summary for prompt injection
    project_summary = "No project summary available yet."
    if db and project_id:
        try:
            from app.services.summary_service import get_summary_content
            project_summary = get_summary_content(project_id, db)
        except Exception:
            pass

    # Initialize the template filler with pattern
    filler = LLMTemplateFiller(pattern=crs_pattern)

    # Fill the CRS template
    result = filler.fill_template(
        user_input=user_input,
        conversation_history=conversation_history,
        extracted_fields=extracted_fields,
        document_context=document_context,
        project_summary=project_summary,
    )

    # Build response message
    # Build response message only if complete
    if result["is_complete"]:
        response = (
            "✅ I've generated a complete CRS document based on your requirements.\n\n"
        )
        response += "**Summary:**\n"
        for point in result["summary_points"]:
            response += f"• {point}\n"
        response += f"\n{result['overall_summary']}"

        persisted = None
        # Persist CRS only when we have a database session, project, and user context
        if db and project_id and user_id:
            persisted = persist_crs_document(
                db=db,
                project_id=project_id,
                created_by=user_id,
                content=result["crs_content"],
                summary_points=result["summary_points"],
                pattern=crs_pattern,
            )

        return {
            "crs_content": result["crs_content"],
            "crs_template": result["crs_template"],
            "summary_points": result["summary_points"],
            "extracted_fields": result["crs_template"],
            "output": response,
            "last_node": "template_filler",
            "crs_is_complete": result["is_complete"],
            "crs_document_id": persisted.id if persisted else None,
            "crs_version": persisted.version if persisted else None,
        }

    # If not complete, update state silently (preserve previous output)
    return {
        "crs_content": result["crs_content"],
        "crs_template": result["crs_template"],
        "summary_points": result["summary_points"],
        "extracted_fields": result["crs_template"],
        "last_node": "template_filler",
        "crs_is_complete": result["is_complete"],
    }
