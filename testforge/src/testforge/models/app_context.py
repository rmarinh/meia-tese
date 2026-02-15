"""Application context model — persistent knowledge about a target application."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from testforge.models.test_model import EndpointMap


class RunRecord(BaseModel):
    """Record of a single pipeline run."""

    run_id: str
    mode: str  # "golden", "observer", "combined"
    timestamp: datetime = Field(default_factory=datetime.now)
    tests_generated: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    endpoints_tested: list[str] = []
    new_coverage: list[str] = []  # endpoints tested for the first time
    issues_found: list[str] = []


class AppContext(BaseModel):
    """Persistent context about a target application.

    Accumulates knowledge across multiple pipeline runs: discovered endpoints,
    learned patterns, coverage gaps, historical test results, etc.
    """

    app_id: str
    app_name: str
    base_url: str
    description: str = ""

    # Accumulated endpoint knowledge (merged from golden + observer runs)
    endpoint_map: EndpointMap | None = None

    # Learned patterns from golden examples
    known_patterns: list[str] = []
    known_fixtures: list[str] = []
    known_test_names: list[str] = []  # avoid regenerating same tests

    # Coverage tracking
    tested_endpoints: list[str] = []  # "METHOD /path" format
    untested_endpoints: list[str] = []
    coverage_gaps: list[str] = []  # identified but not yet tested scenarios

    # Historical results
    total_tests_generated: int = 0
    total_tests_passed: int = 0
    total_tests_failed: int = 0
    run_history: list[RunRecord] = []

    # Application-specific notes the LLM can use for better generation
    notes: list[str] = []

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
