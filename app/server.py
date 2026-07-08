"""FastAPI server exposing the guardrailed agent orchestrator.

Replaces the demo() script with a real HTTP API so the policy-guarded agent
can be called programmatically — the foundation the red-team harness and any
downstream integration build on.

Endpoints:
  POST /tasks          — submit a task to the guarded orchestrator, get the AgentResponse
  GET  /health         — liveness probe
  GET  /policy         — inspect the active policy (checks, allowed_models, fail_action)
  POST /policy/reload  — hot-reload the policy file without restart

The orchestrator, guardrail engine, and policy manager are singletons built
once at startup (the policy file is read once, reloadable on demand).
"""
from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent.orchestrator import AgentOrchestrator
from app.agent.types import Task
from app.evaluation.metrics import EvaluationTracker
from app.guardrails.manager import PolicyManager
from app.guardrails.policy import GuardrailEngine, GuardrailViolation
from app.logging.audit import AuditLogger
from app.tools.base import DataLookupTool
from app.utils.config import EnvironmentConfig

POLICY_PATH = "policies/default.yaml"


def build_orchestrator() -> AgentOrchestrator:
    """Construct the orchestrator with the active policy. Called once at startup."""
    config = EnvironmentConfig.from_env()
    policy_manager = PolicyManager(POLICY_PATH)
    return AgentOrchestrator(
        tools={"data_lookup": DataLookupTool()},
        guardrail_engine=GuardrailEngine(policy_manager=policy_manager),
        audit_logger=AuditLogger(log_path=config.audit_log_path),
        evaluation_tracker=EvaluationTracker(),
        config=config,
    )


app = FastAPI(title="Guardrailed LLM Agent System", version="1.0.0")

# Singletons — built lazily on first request so importing this module has no
# side effects (important for testing).
_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = build_orchestrator()
    return _orchestrator


# ── Request/response models ─────────────────────────────────────────────────

class TaskRequest(BaseModel):
    """Inbound task for the guarded agent."""
    description: str = Field(..., description="What the agent should do")
    role: str = Field("analyst", description="Caller role (audits)")
    model: str | None = Field(None, description="Requested model (checked against allowed_models)")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """The agent's structured response."""
    task_id: str
    status: str
    summary: str
    safety_score: float


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/policy")
def get_policy() -> dict:
    pm = get_orchestrator().guardrail_engine.policy_manager
    p = pm.get_policy().policy
    return {
        "name": p.name,
        "version": p.version,
        "allowed_models": p.allowed_models,
        "checks": p.checks,
        "fail_action": p.fail_action,
    }


@app.post("/policy/reload")
def reload_policy() -> dict:
    """Hot-reload the policy file without restarting the server."""
    pm = get_orchestrator().guardrail_engine.policy_manager
    pm.reload()
    return {"status": "reloaded", **get_policy()}


@app.post("/tasks", response_model=TaskResponse)
def submit_task(req: TaskRequest) -> TaskResponse:
    """Submit a task through the guardrail engine and orchestrator.

    Guardrail violations (PII, disallowed model, tone) surface as HTTP 422
    so callers can distinguish policy blocks from processing errors.
    """
    orch = get_orchestrator()
    params = dict(req.parameters)
    if req.model:
        params["model"] = req.model

    task = Task(
        task_id=f"task-{uuid.uuid4().hex[:8]}",
        description=req.description,
        role=req.role,
        parameters=params,
    )

    try:
        response = orch.run_task(task)
    except GuardrailViolation as e:
        raise HTTPException(status_code=422, detail=f"guardrail violation: {e}")

    return TaskResponse(
        task_id=response.task_id,
        status=response.status,
        summary=response.summary,
        safety_score=response.safety_score,
    )
