"""Models for test execution and validation results."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TestResult(BaseModel):
    """Result from executing a single test."""

    test_name: str
    status: Literal["passed", "failed", "error", "skipped", "timeout"]
    duration_seconds: float = 0.0
    stdout: str = ""
    stderr: str = ""
    error_message: str | None = None
    traceback: str | None = None
    executed_at: datetime = Field(default_factory=datetime.now)


class ExecutionResult(BaseModel):
    """Result from executing a full test suite."""

    suite_name: str
    test_results: list[TestResult] = []
    total_duration_seconds: float = 0.0
    executed_at: datetime = Field(default_factory=datetime.now)
    environment: dict[str, str] = {}

    @property
    def passed(self) -> int:
        return sum(1 for t in self.test_results if t.status == "passed")

    @property
    def failed(self) -> int:
        return sum(1 for t in self.test_results if t.status == "failed")

    @property
    def errors(self) -> int:
        return sum(1 for t in self.test_results if t.status == "error")

    @property
    def pass_rate(self) -> float:
        total = len(self.test_results)
        if total == 0:
            return 0.0
        return self.passed / total


class QualityScore(BaseModel):
    """Quality assessment for a single generated test."""

    test_name: str
    assertion_count: int = 0
    assertion_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    coverage_breadth: float = Field(default=0.0, ge=0.0, le=1.0)
    readability: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    issues: list[str] = []
    suggestions: list[str] = []


class ValidationResult(BaseModel):
    """Aggregated validation result for a test suite."""

    suite_name: str
    execution_result: ExecutionResult | None = None
    quality_scores: list[QualityScore] = []
    flaky_tests: list[str] = []
    avg_quality_score: float = 0.0
    summary: str = ""
    metadata: dict[str, Any] = {}
