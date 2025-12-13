"""Configuration utilities for the agent system.

This module keeps environment-based configuration centralized and
provider-agnostic so the agent can be deployed in multiple environments
without code changes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class EnvironmentConfig:
    """Runtime configuration sourced from environment variables."""

    max_steps: int = 6
    step_timeout_seconds: int = 20
    audit_log_path: Optional[str] = os.getenv("AUDIT_LOG_PATH")
    environment: str = os.getenv("APP_ENV", "development")

    @classmethod
    def from_env(cls) -> "EnvironmentConfig":
        return cls(
            max_steps=int(os.getenv("AGENT_MAX_STEPS", cls.max_steps)),
            step_timeout_seconds=int(
                os.getenv("AGENT_STEP_TIMEOUT_SECONDS", cls.step_timeout_seconds)
            ),
            audit_log_path=os.getenv("AUDIT_LOG_PATH"),
            environment=os.getenv("APP_ENV", "development"),
        )
