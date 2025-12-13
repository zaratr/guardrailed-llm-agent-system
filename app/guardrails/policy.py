"""Guardrail engine enforcing policy constraints."""
from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

from app.agent.types import Task


class GuardrailViolation(Exception):
    """Raised when guardrail checks fail."""


class GuardrailEngine:
    """Evaluates tool requests and agent outputs against policy."""

    def __init__(self, allowed_tools: Dict[str, Dict], prohibited_patterns: Optional[Dict[str, str]] = None):
        self.allowed_tools = allowed_tools
        self.prohibited_patterns = {
            "prompt_injection": r"(?i)ignore previous instructions|override safety",
            "credentials": r"AKIA[0-9A-Z]{16}",
        }
        if prohibited_patterns:
            self.prohibited_patterns.update(prohibited_patterns)

    def assert_task_safe(self, task: Task) -> None:
        for pattern_name, pattern in self.prohibited_patterns.items():
            if re.search(pattern, task.description):
                raise GuardrailViolation(f"Task rejected due to {pattern_name} policy.")

    def inspect_tool_request(self, task: Task, tool_name: Optional[str], tool_input: Dict) -> Tuple[bool, Optional[str]]:
        if tool_name is None:
            return False, None

        if tool_name not in self.allowed_tools:
            return True, "unauthorized_tool"

        tool_policy = self.allowed_tools[tool_name]
        allowed_roles = tool_policy.get("roles", [])
        if allowed_roles and task.role not in allowed_roles:
            return True, "role_not_permitted"

        for pattern_name, pattern in self.prohibited_patterns.items():
            for value in tool_input.values():
                if isinstance(value, str) and re.search(pattern, value):
                    return True, pattern_name

        return False, None

    def inspect_output(self, output: str) -> Tuple[bool, Optional[str]]:
        for pattern_name, pattern in self.prohibited_patterns.items():
            if re.search(pattern, output):
                return True, pattern_name
        return False, None
