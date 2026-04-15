"""
Input sanitization utilities to prevent NoSQL injection attacks.
"""
import logging
from typing import Any, Dict, List

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# MongoDB operators that can be used for injection attacks.
# These allow arbitrary JavaScript execution or can bypass query logic.
_DANGEROUS_OPERATORS = frozenset({
    "$where",
    "$expr",
    "$function",
    "$accumulator",
    "$merge",
    "$out",
    "$lookup",
    "$graphLookup",
    "$unionWith",
    "$currentOp",
    "$listSessions",
    "$collStats",
})


def _check_value(value: Any, path: str = "") -> None:
    """Recursively check a value for dangerous MongoDB operators."""
    if isinstance(value, dict):
        for key, val in value.items():
            current_path = f"{path}.{key}" if path else key
            if key.lower() in _DANGEROUS_OPERATORS:
                logger.warning(
                    "Blocked dangerous MongoDB operator '%s' at path '%s'",
                    key,
                    current_path,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Operator '{key}' is not allowed in queries",
                )
            _check_value(val, current_path)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _check_value(item, f"{path}[{i}]")


def sanitize_query(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a MongoDB query/filter dict and reject dangerous operators.

    Raises HTTPException(400) if dangerous operators are found.
    Returns the query unchanged if safe.
    """
    _check_value(query)
    return query


def sanitize_pipeline(pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate a MongoDB aggregation pipeline and reject dangerous stages.

    Blocks stages that can write data, execute JS, or access other collections.
    """
    dangerous_stages = frozenset({
        "$out",
        "$merge",
        "$lookup",
        "$graphLookup",
        "$unionWith",
        "$currentOp",
        "$listSessions",
        "$collStats",
        "$function",
    })

    for i, stage in enumerate(pipeline):
        for key in stage:
            if key.lower() in dangerous_stages:
                logger.warning(
                    "Blocked dangerous aggregation stage '%s' at pipeline[%d]",
                    key,
                    i,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Aggregation stage '{key}' is not allowed",
                )
        # Also check values within each stage for nested injection
        _check_value(stage, f"pipeline[{i}]")

    return pipeline


# Minimum password requirements
_MIN_PASSWORD_LENGTH = 8


def validate_password_strength(password: str) -> None:
    """
    Validate that a password meets minimum strength requirements.

    Raises HTTPException(400) if the password is too weak.
    """
    if len(password) < _MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {_MIN_PASSWORD_LENGTH} characters long",
        )
