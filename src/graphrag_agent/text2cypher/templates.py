from typing import Dict
from .intent_classifier import QuestionIntent


CYPHERS: Dict[QuestionIntent, str] = {
    QuestionIntent.API_BY_MODULE: """
MATCH (m:Entity {type: 'Module', name: $module_name})<-[:RELATION {type: 'BELONGS_TO'}]-(api:Entity {type: 'API'})
RETURN api.name AS api_name, api.properties.description AS description
""",
    QuestionIntent.ROLES_BY_PERMISSION: """
MATCH (perm:Entity {type: 'Permission', name: $permission_name})
<-[:RELATION {type: 'REQUIRES_PERMISSION'}]-(role:Entity {type: 'Role'})
RETURN role.name AS role_name
""",
    QuestionIntent.WORKFLOW_STEPS: """
MATCH (wf:Entity {type: 'Workflow', name: $workflow_name})-[:RELATION {type: 'HAS_STEP'}]->(s:Entity {type: 'Step'})
OPTIONAL MATCH (s)-[:RELATION {type: 'NEXT_STEP'}]->(next:Entity {type: 'Step'})
RETURN s.name AS step_name, s.properties.order AS step_order, next.name AS next_step
ORDER BY s.properties.order
""",
    QuestionIntent.ERROR_SOLUTION: """
MATCH (err:Entity {type: 'ErrorCode', name: $error_name})
OPTIONAL MATCH (err)-[:RELATION {type: 'CAUSES'}]->(cause:Entity)
OPTIONAL MATCH (err)-[:RELATION {type: 'SOLVED_BY'}]->(solution:Entity)
RETURN err.name AS error, cause.name AS cause, solution.name AS solution
""",
    QuestionIntent.BUSINESS_OBJECT_RELATION: """
MATCH (bo:Entity {type: 'BusinessObject', name: $object_name})-[:RELATION]-(related:Entity)
RETURN related.name AS related_name, related.type AS related_type
""",
}


def get_template(intent: QuestionIntent) -> str:
    return CYPHERS.get(intent, "")
