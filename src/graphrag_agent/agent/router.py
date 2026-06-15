from typing import List, Optional
from graphrag_agent.text2cypher.intent_classifier import IntentClassifier, QuestionIntent


class Router:
    def __init__(self):
        self.classifier = IntentClassifier()

    def decide_mode(self, question: str) -> str:
        intent = self.classifier.classify(question)

        if intent in {
            QuestionIntent.API_BY_MODULE,
            QuestionIntent.WORKFLOW_STEPS,
            QuestionIntent.ROLES_BY_PERMISSION,
            QuestionIntent.BUSINESS_OBJECT_RELATION,
        }:
            return "graph"

        if intent == QuestionIntent.ERROR_SOLUTION:
            return "hybrid"

        return "vector"

    def select_tools(self, mode: str) -> List[str]:
        if mode == "graph":
            return ["generate_cypher", "query_neo4j"]
        if mode == "vector":
            return ["search_vector_db"]
        if mode == "hybrid":
            return ["generate_cypher", "query_neo4j", "search_vector_db"]
        return ["search_vector_db"]
