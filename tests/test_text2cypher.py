from graphrag_agent.text2cypher.intent_classifier import IntentClassifier, QuestionIntent
from graphrag_agent.text2cypher.generator import CypherGenerator


def test_classify_api_by_module():
    clf = IntentClassifier()
    assert clf.classify("Which APIs are in the procurement module?") == QuestionIntent.API_BY_MODULE


def test_classify_workflow_steps():
    clf = IntentClassifier()
    assert clf.classify("What are the steps in the purchase workflow?") == QuestionIntent.WORKFLOW_STEPS


def test_classify_roles_by_permission():
    clf = IntentClassifier()
    assert clf.classify("Which roles can approve purchase orders?") == QuestionIntent.ROLES_BY_PERMISSION


def test_generator_produces_cypher():
    gen = CypherGenerator()
    result = gen.generate(
        "Which APIs are in the procurement module?",
        {"module_name": "Procurement"},
    )
    assert result["intent"] == "api_by_module"
    assert result["confidence"] == 0.85
    assert "MATCH" in result["cypher"]
    assert "'Procurement'" in result["cypher"]


def test_generator_unknown_fallback():
    gen = CypherGenerator()
    result = gen.generate("What is the weather today?")
    assert result["cypher"] == ""
    assert result["confidence"] == 0.0
