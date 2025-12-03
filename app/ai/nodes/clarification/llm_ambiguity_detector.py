from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json
import os
from openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


@dataclass
class Ambiguity:
    type: str
    field: str
    reason: str
    severity: str
    suggestion: Optional[str] = None


class LLMAmbiguityDetector:
    """
    Pure LLM-based ambiguity detector using xAI Grok models.
    """

    ANALYSIS_PROMPT = """
You are a senior Business Analyst...

(keep your prompt here)
"""

    QUESTION_PROMPT = """
You are a Business Analyst generating follow-up questions...

(keep your prompt here)
"""

    def __init__(self, model="grok-2-latest", temperature=0.2):
        if not os.getenv("XAI_API_KEY"):
            raise ValueError("XAI_API_KEY not set in environment.")

        # Connect to xAI Grok API
        self.client = OpenAI(
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1"
        )

        self.model = model
        self.temperature = temperature
        self.parser = JsonOutputParser()

        self.analysis_prompt = ChatPromptTemplate.from_template(self.ANALYSIS_PROMPT)
        self.question_prompt = ChatPromptTemplate.from_template(self.QUESTION_PROMPT)

    # -----------------------------------------
    # LLM wrapper
    # -----------------------------------------
    def _call_llm(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message.content

    # -----------------------------------------
    # Main Analysis
    # -----------------------------------------
    def analyze(self, user_input: str, context: Dict[str, Any]):

        messages = self.analysis_prompt.format_messages(
            user_input=user_input,
            conversation_history="\n".join(context.get("conversation_history", [])),
            extracted_fields=json.dumps(context.get("extracted_fields", {}), indent=2)
        )

        raw = self._call_llm(messages)

        result = self.parser.parse(raw)

        ambiguities = [
            Ambiguity(
                type=a["type"],
                field=a["field"],
                reason=a["reason"],
                severity=a["severity"],
                suggestion=a.get("suggestion")
            )
            for a in result.get("ambiguities", [])
        ]

        return ambiguities, result["overall_clarity_score"], result["summary"]

    # -----------------------------------------
    # Question generation
    # -----------------------------------------
    def generate_questions(self, ambiguities: List[Ambiguity]):
        if not ambiguities:
            return []

        ambiguity_json = json.dumps([{
            "type": a.type,
            "field": a.field,
            "reason": a.reason,
            "severity": a.severity,
            "suggestion": a.suggestion
        } for a in ambiguities], indent=2)

        messages = self.question_prompt.format_messages(
            ambiguity_json=ambiguity_json
        )

        raw = self._call_llm(messages)
        result = self.parser.parse(raw)

        return result["questions"]

    # -----------------------------------------
    # Combined function used by graph node
    # -----------------------------------------
    def analyze_and_generate_questions(self, user_input: str, context: Dict[str, Any]):
        ambiguities, clarity_score, summary = self.analyze(user_input, context)
        questions = self.generate_questions(ambiguities)

        return {
            "ambiguities": ambiguities,
            "clarification_questions": questions,
            "clarity_score": clarity_score,
            "summary": summary,
            "needs_clarification": len(questions) > 0
        }
