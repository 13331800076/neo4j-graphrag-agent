from typing import Optional, Dict, Any
from .intent_classifier import IntentClassifier, QuestionIntent
from .templates import get_template


class CypherGenerator:
    def __init__(self):
        self.classifier = IntentClassifier()

    def generate(self, question: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        parameters = parameters or {}
        intent = self.classifier.classify(question)
        template = get_template(intent)

        if not template or intent == QuestionIntent.UNKNOWN:
            return {
                "cypher": "",
                "intent": intent.value,
                "confidence": 0.0,
                "parameters": parameters,
            }

        cypher = template
        for key, value in parameters.items():
            placeholder = f"${key}"
            if isinstance(value, str):
                cypher = cypher.replace(placeholder, f"'{value}'")
            else:
                cypher = cypher.replace(placeholder, str(value))

        return {
            "cypher": cypher.strip(),
            "intent": intent.value,
            "confidence": 0.85,
            "parameters": parameters,
        }
