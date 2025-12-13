"""Tool base class with strict input/output validation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ToolValidationError(Exception):
    """Raised when tool validation fails."""


class Tool(ABC):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

    def validate_input(self, payload: Dict[str, Any]) -> None:
        missing = [field for field, required in self.input_schema.items() if required and field not in payload]
        if missing:
            raise ToolValidationError(f"Missing required input fields: {missing}")

    def validate_output(self, payload: Dict[str, Any]) -> None:
        missing = [field for field, required in self.output_schema.items() if required and field not in payload]
        if missing:
            raise ToolValidationError(f"Tool produced incomplete output: {missing}")

    @abstractmethod
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with validated input."""


class DataLookupTool(Tool):
    """Example read-only data lookup tool."""

    name = "data_lookup"
    description = "Returns synthetic records for demonstration purposes."
    input_schema = {"query": True}
    output_schema = {"results": True, "complete": True}

    def __init__(self, dataset: List[Dict[str, Any]] | None = None) -> None:
        self.dataset = dataset or [
            {"id": "user-1", "name": "Alice", "status": "active"},
            {"id": "user-2", "name": "Bob", "status": "suspended"},
        ]

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        query = payload.get("query", "").lower()
        matched = [row for row in self.dataset if query in row.get("name", "").lower() or query in row.get("id", "").lower()]
        return {"results": matched, "complete": True}
