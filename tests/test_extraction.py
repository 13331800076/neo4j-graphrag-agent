from graphrag_agent.ingestion.document import Document
from graphrag_agent.extraction.rule_extractor import RuleExtractor
from graphrag_agent.ontology.schema import EntityType, RelationType


def test_extract_from_sample_document():
    doc = Document(
        doc_id="procurement",
        title="Procurement Module",
        source="tests/fixtures/sample_procurement.md",
        text="""# Procurement Module

The procurement module handles purchase orders and supplier management.

## APIs

- `createPurchaseOrder` - Creates a new purchase order.
- `querySupplier` - Queries supplier information.

## Roles

- Procurement Clerk - Requires PURCHASE_CREATE permission.
- Procurement Manager - Requires PURCHASE_APPROVE permission.

## Workflow

1. Submit Request
2. Manager Approval
3. Create Order
4. Inventory Receiving
""",
    )
    extractor = RuleExtractor()
    result = extractor.extract(doc)

    entity_types = {e.type for e in result.entities}
    assert EntityType.MODULE in entity_types
    assert EntityType.API in entity_types
    assert EntityType.ROLE in entity_types
    assert EntityType.PERMISSION in entity_types
    assert EntityType.WORKFLOW in entity_types
    assert EntityType.STEP in entity_types

    # Check relations
    relation_types = {r.type for r in result.relations}
    assert RelationType.BELONGS_TO in relation_types
    assert RelationType.REQUIRES_PERMISSION in relation_types
    assert RelationType.HAS_STEP in relation_types
    assert RelationType.NEXT_STEP in relation_types

    # Check module name
    module = next(e for e in result.entities if e.type == EntityType.MODULE)
    assert module.name == "Procurement"

    # Check API count
    apis = [e for e in result.entities if e.type == EntityType.API]
    assert len(apis) == 2

    # Check step count
    steps = [e for e in result.entities if e.type == EntityType.STEP]
    assert len(steps) == 4

    # Check next_step relations
    next_steps = [r for r in result.relations if r.type == RelationType.NEXT_STEP]
    assert len(next_steps) == 3
