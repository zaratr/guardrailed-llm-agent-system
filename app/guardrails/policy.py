import re
from typing import Dict, Optional, Tuple
from app.agent.types import Task
from app.guardrails.manager import PolicyManager


class GuardrailViolation(Exception):
    """Raised when guardrail checks fail."""


class GuardrailEngine:
    """Evaluates constraints based on active policy configuration."""

    def __init__(self, policy_manager: PolicyManager):
        self.policy_manager = policy_manager
        
        # Hardcoded patterns for demonstration of specific checks
        self.patterns = {
            "pii": r"\b\d{3}-\d{2}-\d{4}\b",  # Simple SSN regex
            "hallucination": r"(?i)confidence: low", # Placeholder for hallucination marker
            "tone": r"(?i)shutup|idiot", # Simple toxicity check
        }

    def assert_task_safe(self, task: Task) -> None:
        """Checks if task is allowed by policy."""
        policy = self.policy_manager.get_policy().policy

        # Enforce allowed_models: if the policy lists allowed models and the
        # task requests one not on the list, block it. (Previously parsed but
        # never consulted — now enforced.)
        requested_model = task.parameters.get("model")
        if requested_model and policy.allowed_models:
            if requested_model not in policy.allowed_models:
                raise GuardrailViolation(
                    f"Model '{requested_model}' not in allowed_models: {policy.allowed_models}"
                )

        # Run every enabled check against the task description (not just PII).
        # Previously only PII was checked here; tone/hallucination were only
        # checked against tool inputs — a gap the red-team harness surfaced.
        for check in policy.checks:
            if check in self.patterns and re.search(self.patterns[check], task.description):
                raise GuardrailViolation(f"Task blocked by {check} check")


    def inspect_tool_request(self, task: Task, tool_name: Optional[str], tool_input: Dict) -> Tuple[bool, Optional[str]]:
        """Inspects tool usage against policy."""
        # Existing role checks can be kept if we merge configs, 
        # but for this specific request we focus on the new yaml checks.
        
        policy = self.policy_manager.get_policy().policy
        
        # Check params for pii/tone if enabled
        for check in policy.checks:
            if check in self.patterns:
                 for value in tool_input.values():
                     if isinstance(value, str) and re.search(self.patterns[check], value):
                         return True, f"Policy violation: {check} detected"

        return False, None

    def inspect_output(self, output: str) -> Tuple[bool, Optional[str]]:
        """Inspects agent output."""
        policy = self.policy_manager.get_policy().policy
        
        for check in policy.checks:
            if check in self.patterns:
                if re.search(self.patterns[check], output):
                    if policy.fail_action == "redact":
                         # In a real system, we'd redact. Here we flag it.
                         return True, f"{check} (redaction required)"
                    else:
                         return True, f"{check} violation"
                         
        return False, None
