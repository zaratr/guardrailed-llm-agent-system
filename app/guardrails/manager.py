import yaml
from pathlib import Path
from app.guardrails.models import PolicyConfig, PolicyDefinition

class PolicyManager:
    def __init__(self, policy_path: str):
        self.policy_path = Path(policy_path)
        self.current_policy: PolicyConfig = self.load_policy()

    def load_policy(self) -> PolicyConfig:
        with open(self.policy_path, "r") as f:
            data = yaml.safe_load(f)
        
        # Manually unpack to support dataclasses
        policy_data = data.get("policy", {})
        policy_def = PolicyDefinition(
            name=policy_data.get("name", "unknown"),
            version=policy_data.get("version", "1.0.0"),
            allowed_models=policy_data.get("allowed_models", []),
            checks=policy_data.get("checks", []),
            fail_action=policy_data.get("fail_action", "block")
        )
        return PolicyConfig(policy=policy_def)

    def reload(self):
        """Reloads the policy from disk."""
        print(f"Reloading policy from {self.policy_path}...")
        self.current_policy = self.load_policy()

    def get_policy(self) -> PolicyConfig:
        return self.current_policy
