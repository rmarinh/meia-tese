"""Models for test style guides extracted from golden examples."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class ImportPattern(BaseModel):
    """An observed import pattern from golden tests."""

    module: str
    names: list[str] = []
    alias: str | None = None
    is_from_import: bool = False


class FixturePattern(BaseModel):
    """An observed pytest fixture pattern."""

    name: str
    scope: str = "function"
    params: list[str] = []
    yields: bool = False
    docstring: str | None = None
    body_summary: str = ""


class AssertionPattern(BaseModel):
    """An observed assertion pattern."""

    style: Literal["assert", "assertEqual", "pytest.raises", "custom"]
    pattern: str  # e.g., "assert response.status_code == 200"
    frequency: int = 1


class TestFunctionPattern(BaseModel):
    """Pattern extracted from a single test function."""

    name: str
    docstring: str | None = None
    decorators: list[str] = []
    fixtures_used: list[str] = []
    http_method: str | None = None
    endpoint: str | None = None
    assertions: list[AssertionPattern] = []
    setup_steps: list[str] = []
    body_summary: str = ""
    line_count: int = 0


class GoldenExample(BaseModel):
    """A parsed golden test file."""

    file_path: str
    source_code: str
    imports: list[ImportPattern] = []
    fixtures: list[FixturePattern] = []
    test_functions: list[TestFunctionPattern] = []
    helper_functions: list[str] = []
    class_names: list[str] = []
    metadata: dict[str, Any] = {}


class TestStyleGuide(BaseModel):
    """Aggregated style guide from all golden examples."""

    framework: Literal["pytest", "unittest", "other"] = "pytest"
    http_client: Literal["requests", "httpx", "aiohttp", "test_client", "other"] = "requests"
    naming_convention: Literal["snake_case", "camelCase"] = "snake_case"
    test_prefix: str = "test_"
    class_based: bool = False

    common_imports: list[ImportPattern] = []
    common_fixtures: list[FixturePattern] = []
    common_assertions: list[AssertionPattern] = []
    common_decorators: list[str] = []

    avg_assertions_per_test: float = 0.0
    avg_test_lines: float = 0.0
    uses_docstrings: bool = False
    uses_parametrize: bool = False

    golden_examples: list[GoldenExample] = []
    raw_patterns: dict[str, Any] = {}
