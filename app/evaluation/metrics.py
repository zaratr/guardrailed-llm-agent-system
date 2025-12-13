"""Evaluation and safety scoring for agent tasks."""
from __future__ import annotations

from typing import Dict, List

from app.agent.types import StepResult, Task


class EvaluationTracker:
    """Produces lightweight metrics for each task."""

    def summarize(self, task: Task, steps: List[StepResult]) -> Dict[str, float]:
        blocked_steps = [s for s in steps if s.blocked]
        total_latency = sum(s.latency_ms for s in steps)
        status = "ok" if not blocked_steps else "blocked"
        safety_score = 1.0
        if blocked_steps:
            safety_score = max(0.1, 1 - 0.1 * len(blocked_steps))

        return {
            "task_id": task.task_id,
            "status": status,
            "step_count": len(steps),
            "blocked_steps": len(blocked_steps),
            "latency_ms_total": total_latency,
            "safety_score": safety_score,
            "summary": self._build_summary(task, status, steps),
        }

    def _build_summary(self, task: Task, status: str, steps: List[StepResult]) -> str:
        if status == "blocked":
            violations = [s.violation for s in steps if s.violation]
            violation = violations[-1] if violations else "unknown"
            return f"Task blocked due to guardrail violation: {violation}."
        if steps and steps[-1].tool_output:
            return f"Task completed using {steps[-1].tool_used}."
        return "Task completed without tool execution."
