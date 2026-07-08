"""Tests for the red-team harness and FastAPI server.

These exercise the REAL policy engine (no mocks) against the attack corpus and
the HTTP endpoints. They verify:
  - the harness runs all attacks and classifies outcomes correctly
  - PII attacks are blocked, benign requests pass
  - allowed_models is now enforced (the previously-dead field)
  - the FastAPI /tasks endpoint returns 422 on guardrail violations
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Red-team harness ────────────────────────────────────────────────────────

def test_red_team_suite_runs_all_attacks():
    """The harness must execute every attack in the corpus."""
    from src.red_team_attacker import run_suite, ATTACKS
    results = run_suite()
    assert len(results) == len(ATTACKS), f"expected {len(ATTACKS)} results, got {len(results)}"


def test_pii_attacks_are_blocked():
    """SSN-containing attacks must be blocked by the PII guardrail."""
    from src.red_team_attacker import run_suite
    results = run_suite()
    pii = [r for r in results if r.category == "pii"]
    assert pii, "no pii-category attacks ran"
    for r in pii:
        assert r.blocked, f"pii attack {r.id} was NOT blocked: {r.description}"


def test_benign_requests_pass():
    """A clean request with no PII/toxicity must NOT be blocked."""
    from src.red_team_attacker import run_suite
    results = run_suite()
    benign = [r for r in results if r.category == "benign"]
    assert benign, "no benign attack ran"
    for r in benign:
        assert not r.blocked, f"benign request {r.id} was wrongly blocked"


def test_allowed_models_now_enforced():
    """A disallowed model must be blocked; an allowed one must pass the model check."""
    from src.red_team_attacker import run_suite
    results = run_suite()
    model_tests = [r for r in results if r.category == "disallowed_model"]
    assert len(model_tests) == 2, f"expected 2 model tests, got {len(model_tests)}"
    blocked = [r for r in model_tests if r.blocked]
    allowed = [r for r in model_tests if not r.blocked]
    assert len(blocked) == 1, "expected 1 blocked (disallowed model)"
    assert len(allowed) == 1, "expected 1 allowed (permitted model)"


def test_injection_gaps_are_honest():
    """Prompt-injection attacks have no current pattern — they pass (documented gap).

    This test pins the honest behavior: the harness does NOT pretend to block
    injections it can't detect. If a pattern is later added, update expect_blocked.
    """
    from src.red_team_attacker import run_suite
    results = run_suite()
    injections = [r for r in results if r.category == "prompt_injection"]
    for r in injections:
        assert not r.blocked, (
            f"injection {r.id} was blocked — if you added a pattern, update "
            "expect_blocked in the corpus and this test."
        )


# ── FastAPI server ──────────────────────────────────────────────────────────

def test_health_endpoint():
    from fastapi.testclient import TestClient
    from app.server import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_policy_endpoint_returns_active_policy():
    from fastapi.testclient import TestClient
    from app.server import app
    client = TestClient(app)
    r = client.get("/policy")
    assert r.status_code == 200
    body = r.json()
    assert "pii" in body["checks"]
    assert "gpt-4o" in body["allowed_models"]


def test_tasks_endpoint_blocks_pii():
    """A task containing an SSN must return 422 (guardrail violation)."""
    from fastapi.testclient import TestClient
    from app.server import app
    client = TestClient(app)
    r = client.post("/tasks", json={
        "description": "Process user data: 123-45-6789",
        "role": "analyst",
    })
    assert r.status_code == 422
    assert "guardrail violation" in r.json()["detail"]


def test_tasks_endpoint_blocks_disallowed_model():
    """A task requesting a disallowed model must return 422."""
    from fastapi.testclient import TestClient
    from app.server import app
    client = TestClient(app)
    r = client.post("/tasks", json={
        "description": "Summarize the report",
        "model": "claude-3-opus",  # not in allowed_models
    })
    assert r.status_code == 422
