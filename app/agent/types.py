"""Type definitions for agent tasks and results."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Task:
    """Represents a unit of work for the agent."""

    task_id: str
    description: str
    role: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StepResult:
    """Outcome of a single reasoning step."""

    step: int
    rationale: str
    tool_used: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    tool_output: Optional[Dict[str, Any]]
    latency_ms: float
    blocked: bool = False
    violation: Optional[str] = None


@dataclass
class AgentResponse:
    """Structured output returned to the caller."""

    task_id: str
    status: str
    summary: str
    steps: List[StepResult]
    metrics: Dict[str, Any]
    safety_score: float
    completed_at: datetime = field(default_factory=datetime.utcnow)
