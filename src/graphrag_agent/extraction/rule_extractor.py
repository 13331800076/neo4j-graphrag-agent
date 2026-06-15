import re
from typing import List
from graphrag_agent.ingestion.document import Document
from graphrag_agent.ontology.schema import Entity, Relation, EntityType, RelationType
from .models import ExtractionResult


class RuleExtractor:
    def extract(self, document: Document) -> ExtractionResult:
        entities = []
        relations = []
        text = document.text

        # Extract Module from H1
        module_match = re.search(r"^#\s+(.+)\s+Module", text, re.MULTILINE | re.IGNORECASE)
        if module_match:
            mod_name = module_match.group(1).strip()
            mod_id = f"mod_{self._slug(mod_name)}"
            module = Entity(
                id=mod_id,
                type=EntityType.MODULE,
                name=mod_name,
                properties={"description": f"{mod_name} module"},
                source_doc_id=document.doc_id,
            )
            entities.append(module)

        # Extract APIs from ## APIs section
        api_section = re.search(r"##\s+APIs?\s+(.+?)(?=##|$)", text, re.DOTALL | re.IGNORECASE)
        if api_section:
            api_text = api_section.group(1)
            for line in api_text.splitlines():
                m = re.match(r"-\s+`?([^`]+)`?\s*-\s*(.+)", line)
                if m:
                    api_name = m.group(1).strip()
                    api_desc = m.group(2).strip()
                    api_id = f"api_{self._slug(api_name)}"
                    api_entity = Entity(
                        id=api_id,
                        type=EntityType.API,
                        name=api_name,
                        properties={"description": api_desc},
                        source_doc_id=document.doc_id,
                    )
                    entities.append(api_entity)
                    if module_match:
                        relations.append(Relation(
                            id=f"rel_{api_id}_belongs",
                            type=RelationType.BELONGS_TO,
                            source_id=api_id,
                            target_id=mod_id,
                        ))

        # Extract Roles from ## Roles section
        roles_section = re.search(r"##\s+Roles?\s+(.+?)(?=##|$)", text, re.DOTALL | re.IGNORECASE)
        if roles_section:
            roles_text = roles_section.group(1)
            for line in roles_text.splitlines():
                m = re.match(r"-\s+(.+?)\s*-\s*Requires?\s+(.+)\s+permission", line, re.IGNORECASE)
                if m:
                    role_name = m.group(1).strip()
                    perm_name = m.group(2).strip().upper()
                    role_id = f"role_{self._slug(role_name)}"
                    perm_id = f"perm_{self._slug(perm_name)}"
                    role_entity = Entity(
                        id=role_id,
                        type=EntityType.ROLE,
                        name=role_name,
                        source_doc_id=document.doc_id,
                    )
                    perm_entity = Entity(
                        id=perm_id,
                        type=EntityType.PERMISSION,
                        name=perm_name,
                        source_doc_id=document.doc_id,
                    )
                    entities.append(role_entity)
                    entities.append(perm_entity)
                    relations.append(Relation(
                        id=f"rel_{role_id}_req",
                        type=RelationType.REQUIRES_PERMISSION,
                        source_id=role_id,
                        target_id=perm_id,
                    ))

        # Extract Workflow Steps from numbered lists in ## Workflow section
        workflow_section = re.search(r"##\s+Workflow\s+(.+?)(?=##|$)", text, re.DOTALL | re.IGNORECASE)
        if workflow_section:
            wf_text = workflow_section.group(1)
            wf_name = f"{mod_name} Workflow" if module_match else "Unknown Workflow"
            wf_id = f"wf_{self._slug(wf_name)}"
            wf_entity = Entity(
                id=wf_id,
                type=EntityType.WORKFLOW,
                name=wf_name,
                source_doc_id=document.doc_id,
            )
            entities.append(wf_entity)
            if module_match:
                relations.append(Relation(
                    id=f"rel_{wf_id}_belongs",
                    type=RelationType.BELONGS_TO,
                    source_id=wf_id,
                    target_id=mod_id,
                ))

            steps = []
            for line in wf_text.splitlines():
                m = re.match(r"\d+\.\s+(.+)", line)
                if m:
                    step_name = m.group(1).strip()
                    step_id = f"step_{self._slug(step_name)}_{len(steps)}"
                    step_entity = Entity(
                        id=step_id,
                        type=EntityType.STEP,
                        name=step_name,
                        properties={"order": len(steps) + 1},
                        source_doc_id=document.doc_id,
                    )
                    entities.append(step_entity)
                    steps.append(step_entity)
                    relations.append(Relation(
                        id=f"rel_{wf_id}_has_{step_id}",
                        type=RelationType.HAS_STEP,
                        source_id=wf_id,
                        target_id=step_id,
                    ))

            for i in range(len(steps) - 1):
                relations.append(Relation(
                    id=f"rel_{steps[i].id}_next",
                    type=RelationType.NEXT_STEP,
                    source_id=steps[i].id,
                    target_id=steps[i + 1].id,
                ))

        return ExtractionResult(entities=entities, relations=relations)

    @staticmethod
    def _slug(text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]+", "_", text).lower().strip("_")
