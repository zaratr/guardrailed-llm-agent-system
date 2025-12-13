"""Entrypoint wiring together the orchestrator and components."""
from __future__ import annotations

from app.agent.orchestrator import AgentOrchestrator
from app.agent.types import Task
from app.evaluation.metrics import EvaluationTracker
from app.guardrails.policy import GuardrailEngine
from app.logging.audit import AuditLogger
from app.tools.base import DataLookupTool
from app.utils.config import EnvironmentConfig


def build_orchestrator() -> AgentOrchestrator:
    config = EnvironmentConfig.from_env()
    tools = {"data_lookup": DataLookupTool()}
    guardrails = GuardrailEngine(
        allowed_tools={"data_lookup": {"roles": ["analyst", "admin", "auditor"]}},
    )
    audit_logger = AuditLogger(log_path=config.audit_log_path)
    evaluation_tracker = EvaluationTracker()
    return AgentOrchestrator(
        tools=tools,
        guardrail_engine=guardrails,
        audit_logger=audit_logger,
        evaluation_tracker=evaluation_tracker,
        config=config,
    )


def demo() -> None:
    orchestrator = build_orchestrator()
    task = Task(
        task_id="task-001",
        description="Lookup user-1 account status",
        role="analyst",
    )
    response = orchestrator.run_task(task)
    print("Agent response:", response)
    print("Audit record:", orchestrator.audit_logger.latest_record())


if __name__ == "__main__":
    demo()
