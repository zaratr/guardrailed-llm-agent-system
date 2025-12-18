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
        # For now, we don't have task-level checks in the yaml, keeping existing logic if needed
        # or assuming task level is safe if not specified.
        # But let's check for PII in task description if 'pii' check is enabled.
        policy = self.policy_manager.get_policy().policy
        
        if "pii" in policy.checks:
            if re.search(self.patterns["pii"], task.description):
                 raise GuardrailViolation("Task contains restricted PII")


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
