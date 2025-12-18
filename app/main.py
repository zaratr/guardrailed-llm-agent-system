"""Entrypoint wiring together the orchestrator and components."""
from __future__ import annotations

from app.agent.orchestrator import AgentOrchestrator
from app.agent.types import Task
from app.evaluation.metrics import EvaluationTracker
from app.guardrails.policy import GuardrailEngine
from app.logging.audit import AuditLogger
from app.tools.base import DataLookupTool
from app.utils.config import EnvironmentConfig
from app.guardrails.manager import PolicyManager


def build_orchestrator(policy_manager: PolicyManager) -> AgentOrchestrator:
    config = EnvironmentConfig.from_env()
    tools = {"data_lookup": DataLookupTool()}
    
    guardrails = GuardrailEngine(policy_manager=policy_manager)
    
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
    print("Initializing Policy Manager...")
    policy_manager = PolicyManager("policies/default.yaml")
    orchestrator = build_orchestrator(policy_manager)
    
    # helper to run a task
    def run_check(name: str):
         print(f"\n--- Running Task: {name} ---")
         # Task that might trigger PII check
         task = Task(
             task_id=f"task-{name}",
             description="Process user data: 123-45-6789",  # Has PII
             role="analyst",
         )
         try:
             # Just checking assertions for now as this demo focuses on policy
             orchestrator.guardrail_engine.assert_task_safe(task)
             print("Task allowed.")
         except Exception as e:
             print(f"Task blocked: {e}")

    # 1. Run with initial policy (which has 'pii' check enabled)
    print("\n[Step 1] Initial Policy State:")
    run_check("Test-1")
    
    # 2. Modify policy file to remove pii check
    print("\n[Step 2] Modifying policy file (disabling PII check)...")
    original_config = ""
    with open("policies/default.yaml", "r") as f:
        original_config = f.read()
    
    # Remove 'pii' from checks
    new_config = original_config.replace("- pii", "# - pii")
    with open("policies/default.yaml", "w") as f:
        f.write(new_config)
        
    # 3. Reload policy
    print("\n[Step 3] Hot Reloading Policy...")
    policy_manager.reload()
    
    # 4. Run task again - should pass now
    print("\n[Step 4] Re-running Task Check:")
    run_check("Test-2")
    
    # Cleanup: Restore original file
    with open("policies/default.yaml", "w") as f:
        f.write(original_config)
    print("\n[Cleanup] Restored original policy file.")


if __name__ == "__main__":
    demo()
