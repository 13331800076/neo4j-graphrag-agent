from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class AnswerOutput(BaseModel):
    answer: str
    graph_evidence: List[Dict[str, Any]]
    text_evidence: List[Dict[str, Any]]
    cypher: Optional[str] = None
    tools_used: List[str]
    mode: str


class Answerer:
    def generate_answer(
        self,
        question: str,
        mode: str,
        graph_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        cypher: Optional[str] = None,
        tools_used: List[str] = None,
    ) -> AnswerOutput:
        tools_used = tools_used or []
        graph_evidence = graph_results
        text_evidence = vector_results

        # Build answer from evidence (no LLM, template-based)
        answer_parts = []

        if graph_evidence:
            answer_parts.append("Based on the knowledge graph:")
            for i, record in enumerate(graph_evidence[:5], 1):
                items = ", ".join(f"{k}={v}" for k, v in record.items() if v is not None)
                answer_parts.append(f"{i}. {items}")

        if text_evidence:
            answer_parts.append("\nFrom the documentation:")
            for i, record in enumerate(text_evidence[:3], 1):
                text = record.get("text", "")
                source = record.get("source", "unknown")
                answer_parts.append(f"{i}. [{source}] {text[:200]}")

        if not answer_parts:
            answer = "I could not find relevant information."
        else:
            answer = "\n".join(answer_parts)

        return AnswerOutput(
            answer=answer,
            graph_evidence=graph_evidence,
            text_evidence=text_evidence,
            cypher=cypher,
            tools_used=tools_used,
            mode=mode,
        )
