"""Agent orchestrator implementing the reasoning loop and guardrails."""
from __future__ import annotations

import time
from typing import Dict, List, Optional

from app.guardrails.policy import GuardrailEngine
from app.logging.audit import AuditLogger
from app.tools.base import Tool
from app.evaluation.metrics import EvaluationTracker
from app.agent.reasoning import HeuristicPlanner
from app.agent.types import AgentResponse, StepResult, Task
from app.utils.config import EnvironmentConfig


class AgentOrchestrator:
    """Coordinates the reasoning loop, tool calls, and guardrails."""

    def __init__(
        self,
        tools: Dict[str, Tool],
        guardrail_engine: GuardrailEngine,
        audit_logger: AuditLogger,
        evaluation_tracker: EvaluationTracker,
        config: Optional[EnvironmentConfig] = None,
    ) -> None:
        self.tools = tools
        self.guardrail_engine = guardrail_engine
        self.audit_logger = audit_logger
        self.evaluation_tracker = evaluation_tracker
        self.config = config or EnvironmentConfig.from_env()
        self.planner = HeuristicPlanner()

    def run_task(self, task: Task) -> AgentResponse:
        self.audit_logger.start_task(task)
        step_results: List[StepResult] = []
        self.guardrail_engine.assert_task_safe(task)

        for step in range(1, self.config.max_steps + 1):
            planned = self.planner.plan(task, step_results)
            start_time = time.time()

            if planned.should_terminate:
                self.audit_logger.log_reasoning(step, planned.rationale)
                break

            tool_name = planned.tool_name
            tool_input = planned.tool_input or {}
            rationale = planned.rationale

            blocked, violation_reason = self.guardrail_engine.inspect_tool_request(
                task, tool_name, tool_input
            )
            if blocked:
                latency_ms = (time.time() - start_time) * 1000
                step_result = StepResult(
                    step=step,
                    rationale=rationale,
                    tool_used=tool_name,
                    tool_input=tool_input,
                    tool_output=None,
                    latency_ms=latency_ms,
                    blocked=True,
                    violation=violation_reason,
                )
                step_results.append(step_result)
                self.audit_logger.log_step(step_result)
                break

            tool = self.tools.get(tool_name) if tool_name else None
            tool_output = None

            if tool is None and tool_name is not None:
                latency_ms = (time.time() - start_time) * 1000
                step_result = StepResult(
                    step=step,
                    rationale="Requested tool not registered; aborting.",
                    tool_used=tool_name,
                    tool_input=tool_input,
                    tool_output=None,
                    latency_ms=latency_ms,
                    blocked=True,
                    violation="unknown_tool",
                )
                step_results.append(step_result)
                self.audit_logger.log_step(step_result)
                break

            if tool:
                tool.validate_input(tool_input)
                tool_output = tool.run(tool_input)
                tool.validate_output(tool_output)

            latency_ms = (time.time() - start_time) * 1000
            step_result = StepResult(
                step=step,
                rationale=rationale,
                tool_used=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                latency_ms=latency_ms,
            )
            step_results.append(step_result)
            self.audit_logger.log_step(step_result)

            if tool_output and tool_output.get("complete"):
                break

        metrics = self.evaluation_tracker.summarize(task, step_results)
        safety_score = metrics.get("safety_score", 1.0)
        response = AgentResponse(
            task_id=task.task_id,
            status="completed" if metrics.get("status") == "ok" else "blocked",
            summary=metrics.get("summary", "Task processed with guardrails."),
            steps=step_results,
            metrics=metrics,
            safety_score=safety_score,
        )
        self.audit_logger.end_task(response)
        return response
