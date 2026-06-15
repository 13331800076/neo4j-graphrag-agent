from enum import Enum
from typing import Optional
import re


class QuestionIntent(str, Enum):
    API_BY_MODULE = "api_by_module"
    ROLES_BY_PERMISSION = "roles_by_permission"
    WORKFLOW_STEPS = "workflow_steps"
    ERROR_SOLUTION = "error_solution"
    BUSINESS_OBJECT_RELATION = "business_object_relation"
    UNKNOWN = "unknown"


class IntentClassifier:
    def classify(self, question: str) -> QuestionIntent:
        q = question.lower()

        if any(k in q for k in ["api", "interface", "method"]) and any(k in q for k in ["module", "mod"]):
            return QuestionIntent.API_BY_MODULE

        if any(k in q for k in ["role", "who can", "approve", "permission"]):
            return QuestionIntent.ROLES_BY_PERMISSION

        if any(k in q for k in ["step", "flow", "process", "workflow", "from", "next"]):
            return QuestionIntent.WORKFLOW_STEPS

        if any(k in q for k in ["error", "fail", "fix", "solve", "issue"]):
            return QuestionIntent.ERROR_SOLUTION

        if any(k in q for k in ["related", "relation", "connect", "link"]):
            return QuestionIntent.BUSINESS_OBJECT_RELATION

        return QuestionIntent.UNKNOWN
