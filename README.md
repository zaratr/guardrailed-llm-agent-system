# Policy-Guarded LLM Agent with Red-Team Harness

A guardrail-first LLM agent skeleton: a YAML policy engine gates model calls,
an audit log records every decision, and a red-team harness exercises the
agent against a small canned jailbreak corpus. The repository is intentionally
framework-light — it shows the *shape* of a guarded agent (policy load →
check → audit) without depending on a hosted model or a long-running
guardrail server.

## What is actually implemented

| component | status | location |
|---|---|---|
| YAML-driven policy engine (`PolicyManager`, `PolicyConfig`) | implemented | `app/guardrails/manager.py`, `app/guardrails/models.py`, `app/guardrails/policy.py` |
| Default policy (`financial-advice`, PII / hallucination / tone checks, `fail_action: redact`) | implemented | `policies/default.yaml` |
| Agent orchestrator with reasoning + typed tool interface | implemented | `app/agent/orchestrator.py`, `app/agent/reasoning.py`, `app/agent/types.py`, `app/tools/base.py` |
| Evaluation metrics module | scaffolded | `app/evaluation/metrics.py` |
| Structured audit logging | implemented | `app/logging/audit.py` |
| FastAPI entrypoint | scaffolded | `app/main.py` |
| Red-team harness (canned jailbreak corpus) | **stub** — prints attacks; no live model call | `src/red_team_attacker.py` |

## What is NOT implemented (explicitly)

To avoid overstating the system, the following capabilities are **not**
present in this repository:

- **NeMo Guardrails is not wired.** An earlier README named NeMo Guardrails
  as the defense layer; in reality there is no `nemoguardrails` import, no
  `config.yml` rails config, and no Colang flows. The defense layer in this
  repo is the lightweight YAML policy engine above. NeMo integration is
  listed under _Roadmap_ below.
- **The red-team attacker does not invoke a live model.** It iterates a
  three-prompt jailbreak corpus and emits a canned "blocked" line per
  attack. It is a placeholder for a future loop that calls the agent and
  records the actual policy decision.
- **No automated security report generation.** Metrics are scaffolded but
  no report writer persists attack success/failure rates yet.

## Roadmap

1. Replace `src/red_team_attacker.py` with a real attacker loop that calls
   `app.agent.orchestrator` and records the policy decision per attack.
2. Wire NeMo Guardrails as an alternative `GuardrailBackend` behind the
   existing `PolicyManager` interface, with a rails server in `docker/`.
3. Persist evaluation results from `app/evaluation/metrics.py` to a
   JSON/Markdown security report under `reports/`.

## Tech stack

- **Policy layer:** Python, PyYAML, dataclasses
- **Agent skeleton:** Python, FastAPI, typed tool protocol
- **Red-team harness:** Python (stub)
- **Models:** pluggable; no specific LLM pinned
