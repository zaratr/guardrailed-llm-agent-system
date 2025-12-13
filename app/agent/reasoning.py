"""Reasoning strategy for the agent loop.

This module intentionally keeps the planning logic deterministic and auditable
instead of relying on implicit LLM behaviors. The heuristic planner inspects the
incoming task and history to determine the next action and ensures the plan is
explainable in audit logs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .types import StepResult, Task


@dataclass
class PlannedStep:
    """Planned action for the next reasoning iteration."""

    rationale: str
    tool_name: Optional[str]
    tool_input: Optional[Dict]
    should_terminate: bool = False


class HeuristicPlanner:
    """Simple rule-based planner for deterministic behavior.

    In production this could be replaced by an LLM-powered planner that is still
    wrapped in the same guardrail and validation layers.
    """

    def plan(self, task: Task, history: List[StepResult]) -> PlannedStep:
        if history:
            last_step = history[-1]
            if last_step.blocked:
                return PlannedStep(
                    rationale="Guardrails blocked the previous action; terminating to prevent unsafe retries.",
                    tool_name=None,
                    tool_input=None,
                    should_terminate=True,
                )

            if last_step.tool_output and last_step.tool_output.get("complete"):
                return PlannedStep(
                    rationale="Tool indicated completion; wrapping up task.",
                    tool_name=None,
                    tool_input=None,
                    should_terminate=True,
                )

        requested_tool = task.parameters.get("tool")
        if requested_tool:
            rationale = f"Caller requested tool '{requested_tool}'."
            return PlannedStep(rationale=rationale, tool_name=requested_tool, tool_input=task.parameters)

        if "lookup" in task.description.lower():
            return PlannedStep(
                rationale="Task mentions lookup; selecting data_lookup tool.",
                tool_name="data_lookup",
                tool_input={"query": task.description},
            )

        return PlannedStep(
            rationale="No specific tool requested; summarizing as completed with no action.",
            tool_name=None,
            tool_input=None,
            should_terminate=True,
        )
