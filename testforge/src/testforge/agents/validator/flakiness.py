"""Flakiness detection via repeated test execution."""

from __future__ import annotations

import logging

from testforge.agents.executor.runner import ExecutorAgent, ExecutorInput
from testforge.models.test_model import TestSuite

logger = logging.getLogger("testforge.validator.flakiness")


async def detect_flaky_tests(
    test_suite: TestSuite,
    base_url: str,
    runs: int = 3,
) -> list[str]:
    """Run the test suite multiple times and identify tests with inconsistent results.

    Returns list of test names that are flaky (different results across runs).
    """
    if runs < 2:
        return []

    executor = ExecutorAgent()
    results_per_test: dict[str, list[str]] = {}

    for i in range(runs):
        logger.info("Flakiness detection run %d/%d", i + 1, runs)
        executor_input = ExecutorInput(
            test_suite=test_suite,
            base_url=base_url,
        )
        output = await executor.run(executor_input)

        for tr in output.execution_result.test_results:
            results_per_test.setdefault(tr.test_name, []).append(tr.status)

    flaky = []
    for test_name, statuses in results_per_test.items():
        if len(set(statuses)) > 1:
            flaky.append(test_name)
            logger.warning(
                "Flaky test detected: %s — statuses: %s", test_name, statuses
            )

    return flaky
