"""Base agent abstract class for all TestForge agents."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentResult(BaseModel):
    """Wrapper for agent execution results."""

    agent_name: str
    success: bool
    data: dict[str, Any] = {}
    errors: list[str] = []
    warnings: list[str] = []


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all TestForge agents.

    Each agent receives typed input, performs its task, and returns typed output.
    """

    def __init__(self, name: str | None = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"testforge.agents.{self.name}")

    @abstractmethod
    async def run(self, input_data: InputT) -> OutputT:
        """Execute the agent's main task."""
        ...

    async def validate_input(self, input_data: InputT) -> list[str]:
        """Validate input before running. Returns list of error messages."""
        return []

    async def execute(self, input_data: InputT) -> AgentResult:
        """Execute with validation and error handling."""
        errors = await self.validate_input(input_data)
        if errors:
            return AgentResult(
                agent_name=self.name,
                success=False,
                errors=errors,
            )

        try:
            self.logger.info("Starting %s", self.name)
            output = await self.run(input_data)
            self.logger.info("Completed %s", self.name)
            return AgentResult(
                agent_name=self.name,
                success=True,
                data=output.model_dump(),
            )
        except Exception as e:
            self.logger.exception("Agent %s failed", self.name)
            return AgentResult(
                agent_name=self.name,
                success=False,
                errors=[str(e)],
            )
