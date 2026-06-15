import re
from typing import List

ALLOWED_KEYWORDS = {
    "MATCH", "RETURN", "WHERE", "LIMIT", "ORDER", "BY", "AS",
    "WITH", "UNWIND", "COLLECT", "COUNT", "DISTINCT", "OPTIONAL",
    "AND", "OR", "NOT", "IN", "IS", "NULL", "TRUE", "FALSE",
    "STARTS", "ENDS", "CONTAINS", "CASE", "WHEN", "THEN", "ELSE",
}

FORBIDDEN_KEYWORDS = {
    "CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE",
    "DROP", "CALL", "LOAD", "CSV", "apoc", "gds", "dbms",
    "GRANT", "REVOKE", "DENY", "ROLE", "USER", "PASSWORD",
}


class CypherSafetyError(Exception):
    pass


def validate_read_only(cypher: str) -> bool:
    upper = cypher.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in upper:
            raise CypherSafetyError(f"Forbidden keyword detected: {keyword}")
    return True


def sanitize_cypher(cypher: str) -> str:
    cleaned = cypher.strip()
    if not cleaned:
        raise CypherSafetyError("Empty Cypher query")
    validate_read_only(cleaned)
    return cleaned
