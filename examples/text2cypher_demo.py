#!/usr/bin/env python3
"""Demo: Template-based text2cypher."""
from graphrag_agent.text2cypher.generator import CypherGenerator

QUESTIONS = [
    ("Which APIs are in the procurement module?", {"module_name": "Procurement"}),
    ("Which roles can approve purchase orders?", {"permission_name": "PURCHASE_APPROVE"}),
    ("What are the steps in the purchase workflow?", {"workflow_name": "Procurement Workflow"}),
]

def main():
    gen = CypherGenerator()
    for question, params in QUESTIONS:
        result = gen.generate(question, params)
        print(f"Q: {question}")
        print(f"Intent: {result['intent']}")
        print(f"Cypher:\n{result['cypher']}\n")

if __name__ == "__main__":
    main()
