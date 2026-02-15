"""Docker sandbox for isolated test execution (Phase 5)."""

from __future__ import annotations

import logging

logger = logging.getLogger("testforge.executor.sandbox")


class DockerSandbox:
    """Placeholder for Docker-based test execution sandbox.

    Will be implemented in Phase 5 to provide fully isolated test execution.
    """

    def __init__(self, image: str = "python:3.12-slim"):
        self.image = image

    async def run_tests(self, test_file_content: str, requirements: list[str]) -> dict:
        raise NotImplementedError("Docker sandbox is planned for Phase 5")
