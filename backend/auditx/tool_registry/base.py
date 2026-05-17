from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    tool_name: str = Field(min_length=1)
    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, input_data: dict[str, Any]) -> ToolResult:
        raise NotImplementedError
