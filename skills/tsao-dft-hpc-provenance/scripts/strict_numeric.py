#!/usr/bin/env python3
"""Shared fail-closed numeric contracts for resources and acceleration policies."""

from __future__ import annotations

import math
from typing import Any


def exact_int(value: Any, name: str, errors: list[str], minimum: int = 0) -> int:
    """Accept only a real Python integer, excluding bool and lossy coercions."""

    if type(value) is not int:
        errors.append(f"{name} must be an integer")
        return minimum
    if value < minimum:
        errors.append(f"{name} must be >= {minimum}")
    return value


def finite_number(value: Any, name: str, errors: list[str], minimum: float = 0.0) -> float:
    """Accept only finite int/float values, excluding bool and numeric strings."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{name} must be finite numeric")
        return minimum
    rendered = float(value)
    if not math.isfinite(rendered):
        errors.append(f"{name} must be finite numeric")
        return minimum
    if rendered < minimum:
        errors.append(f"{name} must be >= {minimum}")
    return rendered


def exact_int_values(values: Any, default: list[int], *, minimum: int = 1) -> list[int]:
    """Return sorted unique exact integers; invalid items are ignored deterministically."""

    raw = values if isinstance(values, list) and values else default
    result = {value for value in raw if type(value) is int and value >= minimum}
    return sorted(result) or list(default)
