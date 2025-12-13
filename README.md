# Guardrailed LLM Agent System

This project demonstrates a production-grade pattern for building an LLM agent
that operates inside tightly controlled, auditable boundaries. It favors
explicit tools, guardrails, and metrics instead of unrestricted prompt-only
behaviors.

## Architecture

```
/app
  /agent          # Orchestrator, planning, and task types
  /tools          # Explicit tools with schemas and permissions
  /guardrails     # Policy engine enforcing safety and role checks
  /evaluation     # Metrics and safety scoring
  /logging        # Audit logging utilities
  /utils          # Environment-aware configuration helpers
/config           # Deployment configuration placeholders
/scripts         # Operational scripts
/tests           # Future automated tests
```

### Control Flow
1. **Task intake:** A `Task` containing description, role, and parameters is
   provided to the `AgentOrchestrator`.
2. **Guardrail pre-check:** The `GuardrailEngine` rejects tasks containing
   prohibited patterns before any reasoning occurs.
3. **Planning:** A deterministic `HeuristicPlanner` decides the next action and
   emits an auditable rationale.
4. **Authorization:** Guardrails validate the requested tool against allowed
   roles and scan inputs for unsafe content.
5. **Tool execution:** Typed tools validate inputs and outputs. Unauthorized or
   unknown tool requests are blocked.
6. **Observation:** Each step is written to the `AuditLogger`, capturing
   rationale, inputs, outputs, latency, and violations.
7. **Evaluation:** `EvaluationTracker` summarizes safety score, status, and
   latency metrics for the task response.

### Guardrails
- **Pattern detection:** Blocks prompt-injection keywords, credential-like
  strings, and other configurable patterns.
- **Role-based permissions:** Each tool declares allowed roles; the guardrail
  engine denies requests outside those roles.
- **Validation hooks:** Tool input/output schemas are validated explicitly to
  prevent malformed interactions.
- **Termination rules:** The planner and orchestrator stop after a configurable
  number of steps or when violations occur.

### Tool Permissions
Tools are explicitly registered with the orchestrator alongside a policy
configuration indicating which roles may invoke them. Attempting to call an
unregistered or unauthorized tool results in a guardrail violation before any
execution occurs.

### Evaluation & Audit Logging
`EvaluationTracker` computes per-task metrics including step count, blocked
steps, and safety score. `AuditLogger` stores a per-task trace that includes all
reasoning steps, tool inputs/outputs, and guardrail decisions. If an
`AUDIT_LOG_PATH` environment variable is set, records are also appended to that
file in JSON-lines format for downstream analysis.

### Configuration and Extensibility
- Environment variables such as `AGENT_MAX_STEPS` and `AGENT_STEP_TIMEOUT_SECONDS`
  tune runtime behavior without code changes.
- LLM provider calls can be added behind the planner while retaining the same
  guardrail enforcement and tool validation layers.
- Additional tools can be defined by subclassing `Tool` and updating the
  `GuardrailEngine` configuration with role permissions and validation rules.
- Production deployments can extend guardrails with data redaction, PII
  detection, rate limiting, or external policy engines.

## Getting Started

1. Ensure Python 3.11+ is available.
2. Run the demo to execute a sample guardrailed task:
   ```bash
   python -m app.main
   ```
3. Inspect the in-memory audit record printed to the console or configure
   `AUDIT_LOG_PATH` to persist JSON traces for compliance needs.

## Security and Safety Considerations
- All behavior flows through explicit tools; no direct system access is
  permitted.
- Guardrails reject suspicious inputs early and block unpermitted tool usage.
- Safety scoring highlights when interventions occur, enabling monitoring of
  unsafe action attempts.
- The deterministic planner makes reasoning transparent and auditable; replacing
  it with an LLM-powered planner should maintain these control surfaces.

## Next Steps for Production
- Integrate an actual LLM behind the planner with constrained tool selection
  prompts.
- Expand guardrails to include DLP/PII scanning, allow/deny lists, and external
  policy services.
- Add automated evaluations and load tests in `/tests` to track regression in
  safety metrics.
- Ship audit logs to centralized observability platforms and wire alerts for
  repeated guardrail violations.
