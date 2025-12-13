"""Audit logging utilities."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agent.types import AgentResponse, StepResult, Task


class AuditLogger:
    """Collects auditable traces for every task."""

    def __init__(self, log_path: Optional[str] = None) -> None:
        self.log_path = log_path
        self.records: List[Dict[str, Any]] = []

    def start_task(self, task: Task) -> None:
        entry = {
            "task_id": task.task_id,
            "role": task.role,
            "description": task.description,
            "parameters": task.parameters,
            "started_at": datetime.utcnow().isoformat(),
            "steps": [],
        }
        self.records.append(entry)

    def log_reasoning(self, step: int, rationale: str) -> None:
        if not self.records:
            return
        self.records[-1]["steps"].append(
            {"step": step, "rationale": rationale, "event": "planner"}
        )

    def log_step(self, result: StepResult) -> None:
        if not self.records:
            return
        self.records[-1]["steps"].append(
            {
                "step": result.step,
                "rationale": result.rationale,
                "tool": result.tool_used,
                "tool_input": result.tool_input,
                "tool_output": result.tool_output,
                "latency_ms": result.latency_ms,
                "blocked": result.blocked,
                "violation": result.violation,
            }
        )

    def end_task(self, response: AgentResponse) -> None:
        if not self.records:
            return
        self.records[-1].update(
            {
                "completed_at": response.completed_at.isoformat(),
                "status": response.status,
                "summary": response.summary,
                "safety_score": response.safety_score,
                "metrics": response.metrics,
            }
        )
        if self.log_path:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(self.records[-1]) + "\n")

    def latest_record(self) -> Optional[Dict[str, Any]]:
        return self.records[-1] if self.records else None
