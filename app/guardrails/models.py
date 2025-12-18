from dataclasses import dataclass, field
from typing import List

@dataclass
class PolicyDefinition:
    name: str
    allowed_models: List[str]
    checks: List[str]
    fail_action: str
    version: str = "1.0.0"

@dataclass
class PolicyConfig:
    policy: PolicyDefinition
