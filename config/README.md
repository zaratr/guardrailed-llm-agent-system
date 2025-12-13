# Configuration

Environment variables control runtime behavior without code changes:
- `AGENT_MAX_STEPS`: Maximum reasoning iterations per task (default 6).
- `AGENT_STEP_TIMEOUT_SECONDS`: Maximum duration allowed for a step (default 20).
- `AUDIT_LOG_PATH`: Optional file path for JSON-lines audit logs.
- `APP_ENV`: Environment label (e.g., development, staging, production).

Extend this folder with environment-specific policy files (e.g., allowlists,
redaction rules) that can be loaded by `GuardrailEngine` in production.
