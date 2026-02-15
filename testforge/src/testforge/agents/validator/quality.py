"""Validator Agent — checks test quality and scores results."""

from __future__ import annotations

import re

from pydantic import BaseModel

from testforge.agents.base import BaseAgent
from testforge.models.results import ExecutionResult, QualityScore, ValidationResult
from testforge.models.test_model import GeneratedTest, TestSuite


class ValidatorInput(BaseModel):
    """Input for the Validator Agent."""

    test_suite: TestSuite
    execution_result: ExecutionResult | None = None
    flakiness_runs: int = 0  # number of re-runs for flakiness check


class ValidatorOutput(BaseModel):
    """Output of the Validator Agent."""

    validation_result: ValidationResult


class ValidatorAgent(BaseAgent[ValidatorInput, ValidatorOutput]):
    """Validates generated tests for quality, correctness, and flakiness."""

    def __init__(self):
        super().__init__("ValidatorAgent")

    async def run(self, input_data: ValidatorInput) -> ValidatorOutput:
        quality_scores = [
            self._score_test(test) for test in input_data.test_suite.tests
        ]

        avg_score = 0.0
        if quality_scores:
            avg_score = sum(q.overall_score for q in quality_scores) / len(quality_scores)

        summary_parts = [
            f"Tests: {len(input_data.test_suite.tests)}",
            f"Avg quality: {avg_score:.2f}",
        ]

        if input_data.execution_result:
            er = input_data.execution_result
            summary_parts.extend([
                f"Passed: {er.passed}/{len(er.test_results)}",
                f"Pass rate: {er.pass_rate:.0%}",
            ])

        return ValidatorOutput(
            validation_result=ValidationResult(
                suite_name=input_data.test_suite.name,
                execution_result=input_data.execution_result,
                quality_scores=quality_scores,
                avg_quality_score=avg_score,
                summary=" | ".join(summary_parts),
            )
        )

    def _score_test(self, test: GeneratedTest) -> QualityScore:
        """Score a single test's quality."""
        code = test.source_code
        issues: list[str] = []
        suggestions: list[str] = []

        # Count assertions
        assertion_count = len(re.findall(r"\bassert\b", code))
        if assertion_count == 0:
            issues.append("No assertions found")
            assertion_quality = 0.0
        elif assertion_count == 1:
            assertion_quality = 0.5
            suggestions.append("Consider adding more assertions")
        else:
            assertion_quality = min(1.0, assertion_count / 4)

        # Check for status code assertion
        has_status_check = bool(re.search(r"status_code", code))
        if not has_status_check and test.test_type == "api":
            issues.append("Missing status code assertion")
            assertion_quality *= 0.7

        # Check for response body assertions
        has_body_check = bool(
            re.search(r"\.json\(\)|response\.data|response\.text|response\.content", code)
        )
        if not has_body_check and test.test_type == "api":
            suggestions.append("Consider asserting response body content")

        # Coverage breadth — does it test different aspects?
        breadth_signals = [
            has_status_check,
            has_body_check,
            bool(re.search(r"headers", code)),
            bool(re.search(r"pytest\.raises|Exception|Error", code)),
        ]
        coverage_breadth = sum(breadth_signals) / len(breadth_signals)

        # Readability
        lines = code.strip().split("\n")
        line_count = len(lines)
        has_docstring = bool(re.search(r'""".*?"""|\'\'\'.*?\'\'\'', code, re.DOTALL))

        readability = 0.7  # base
        if has_docstring:
            readability += 0.1
        if line_count > 30:
            readability -= 0.1
            suggestions.append("Test is quite long, consider splitting")
        if line_count < 3:
            readability -= 0.2
            issues.append("Test seems too short")
        readability = max(0.0, min(1.0, readability))

        # Check for hardcoded values that look like they should be variables
        if re.search(r'http://localhost:\d+', code):
            suggestions.append("Consider using a base_url fixture instead of hardcoded URL")

        # Overall score
        overall = (
            assertion_quality * 0.4
            + coverage_breadth * 0.3
            + readability * 0.3
        )

        return QualityScore(
            test_name=test.name,
            assertion_count=assertion_count,
            assertion_quality=assertion_quality,
            coverage_breadth=coverage_breadth,
            readability=readability,
            overall_score=overall,
            issues=issues,
            suggestions=suggestions,
        )
