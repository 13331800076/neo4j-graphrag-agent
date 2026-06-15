from graphrag_agent.agent.router import Router
from graphrag_agent.agent.answerer import Answerer, AnswerOutput
from graphrag_agent.text2cypher.intent_classifier import QuestionIntent


def test_router_graph_mode_for_api_question():
    router = Router()
    mode = router.decide_mode("Which APIs are in the procurement module?")
    assert mode == "graph"
    tools = router.select_tools(mode)
    assert "generate_cypher" in tools
    assert "query_neo4j" in tools


def test_router_hybrid_mode_for_error_question():
    router = Router()
    mode = router.decide_mode("Why does attachment upload fail?")
    assert mode == "hybrid"


def test_router_vector_mode_for_general_question():
    router = Router()
    mode = router.decide_mode("How does the system work?")
    assert mode == "vector"


def test_answerer_with_graph_evidence():
    answerer = Answerer()
    graph_results = [{"api_name": "createPurchaseOrder", "description": "Creates PO"}]
    output = answerer.generate_answer(
        question="Which APIs?",
        mode="graph",
        graph_results=graph_results,
        vector_results=[],
        cypher="MATCH ...",
        tools_used=["generate_cypher", "query_neo4j"],
    )
    assert isinstance(output, AnswerOutput)
    assert "createPurchaseOrder" in output.answer
    assert output.cypher == "MATCH ..."
    assert output.mode == "graph"


def test_answerer_empty_evidence():
    answerer = Answerer()
    output = answerer.generate_answer(
        question="What is X?",
        mode="vector",
        graph_results=[],
        vector_results=[],
    )
    assert "could not find" in output.answer
