"""Models for generated tests and endpoint maps."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class EndpointInfo(BaseModel):
    """Information about a discovered API endpoint."""

    method: str
    path: str
    description: str = ""
    request_schema: dict[str, Any] | None = None
    response_schema: dict[str, Any] | None = None
    auth_required: bool = False
    auth_type: str | None = None
    query_params: list[str] = []
    path_params: list[str] = []
    observed_status_codes: list[int] = []
    sample_request: Any | None = None
    sample_response: Any | None = None


class EndpointMap(BaseModel):
    """Map of all discovered endpoints for an application."""

    app_name: str
    base_url: str
    endpoints: list[EndpointInfo] = []
    auth_patterns: list[str] = []
    common_headers: dict[str, str] = {}
    dependencies: dict[str, list[str]] = {}  # endpoint → depends on endpoints

    @property
    def endpoint_count(self) -> int:
        return len(self.endpoints)


class GeneratedTest(BaseModel):
    """A single generated test case."""

    id: str = ""
    name: str
    description: str = ""
    source_code: str
    test_type: Literal["api", "ui", "integration", "unit"] = "api"
    target_endpoint: str | None = None
    target_method: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    generation_metadata: dict[str, Any] = {}


class TestSuite(BaseModel):
    """A collection of generated tests."""

    name: str
    description: str = ""
    tests: list[GeneratedTest] = []
    setup_code: str = ""  # shared fixtures/setup
    imports_code: str = ""  # shared imports
    conftest_code: str = ""  # conftest.py content
    target_app: str = ""
    base_url: str = ""

    @property
    def test_count(self) -> int:
        return len(self.tests)

    def to_file_content(self) -> str:
        """Render the full test file content."""
        parts = []
        if self.imports_code:
            parts.append(self.imports_code.strip())
        if self.setup_code:
            parts.append(self.setup_code.strip())
        for test in self.tests:
            parts.append(test.source_code.strip())
        return "\n\n\n".join(parts) + "\n"
