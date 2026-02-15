"""Test runner — executes generated tests in subprocess or Docker sandbox."""

from __future__ import annotations

import asyncio
import tempfile
import uuid
from pathlib import Path

from pydantic import BaseModel

from testforge.agents.base import BaseAgent
from testforge.config import settings
from testforge.models.results import ExecutionResult, TestResult
from testforge.models.test_model import TestSuite


class ExecutorInput(BaseModel):
    """Input for the Executor Agent."""

    test_suite: TestSuite
    base_url: str = "http://localhost:5000"
    timeout_seconds: int = 60
    working_dir: str | None = None


class ExecutorOutput(BaseModel):
    """Output of the Executor Agent."""

    execution_result: ExecutionResult
    test_file_path: str = ""


class ExecutorAgent(BaseAgent[ExecutorInput, ExecutorOutput]):
    """Runs generated tests and collects results."""

    def __init__(self):
        super().__init__("ExecutorAgent")

    async def run(self, input_data: ExecutorInput) -> ExecutorOutput:
        # Write test file to disk
        test_dir = Path(input_data.working_dir or tempfile.mkdtemp(prefix="testforge_"))
        test_dir.mkdir(parents=True, exist_ok=True)

        test_file = test_dir / f"test_{input_data.test_suite.name}.py"
        test_content = input_data.test_suite.to_file_content()
        test_file.write_text(test_content, encoding="utf-8")

        # Write conftest — use provided or auto-generate common fixtures
        conftest = test_dir / "conftest.py"
        if input_data.test_suite.conftest_code:
            conftest.write_text(input_data.test_suite.conftest_code, encoding="utf-8")
        else:
            base = input_data.base_url
            conftest_content = (
                'import os\n'
                'import pytest\n'
                'import requests\n\n\n'
                '@pytest.fixture\n'
                'def base_url():\n'
                f'    """Base URL for the API."""\n'
                f'    return os.environ.get("BASE_URL", "{base}")\n\n\n'
                '@pytest.fixture\n'
                'def created_user(base_url):\n'
                '    """Create a user and return its data. Clean up after test."""\n'
                '    payload = {"name": "Test User", "email": f"test_{id(object())}@example.com", "role": "user"}\n'
                '    response = requests.post(f"{base_url}/api/users", json=payload)\n'
                '    assert response.status_code == 201\n'
                '    user = response.json()\n'
                '    yield user\n'
                '    requests.delete(f"{base_url}/api/users/{user[\'id\']}")\n\n\n'
                '@pytest.fixture\n'
                'def sample_user(base_url):\n'
                '    """Create a sample user for testing."""\n'
                '    payload = {"name": "Sample User", "email": f"sample_{id(object())}@example.com", "role": "admin"}\n'
                '    response = requests.post(f"{base_url}/api/users", json=payload)\n'
                '    assert response.status_code == 201\n'
                '    user = response.json()\n'
                '    yield user\n'
                '    requests.delete(f"{base_url}/api/users/{user[\'id\']}")\n'
            )
            conftest.write_text(conftest_content, encoding="utf-8")

        self.logger.info("Test file written: %s", test_file)

        # Run with pytest
        execution_result = await self._run_pytest(
            test_file, input_data.timeout_seconds, input_data.base_url
        )

        return ExecutorOutput(
            execution_result=execution_result,
            test_file_path=str(test_file),
        )

    async def _run_pytest(
        self, test_file: Path, timeout: int, base_url: str
    ) -> ExecutionResult:
        """Run pytest on the test file and parse results."""
        cmd = [
            "python",
            "-m",
            "pytest",
            str(test_file),
            "-v",
            "--tb=short",
        ]

        env_vars = {
            "BASE_URL": base_url,
            "TESTFORGE_RUN": "1",
        }

        import os

        env = {**os.environ, **env_vars}

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=str(test_file.parent),
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            self.logger.info("pytest exit code: %d", proc.returncode)

            test_results = self._parse_pytest_output(stdout, stderr)

            return ExecutionResult(
                suite_name=test_file.stem,
                test_results=test_results,
            )

        except asyncio.TimeoutError:
            return ExecutionResult(
                suite_name=test_file.stem,
                test_results=[
                    TestResult(
                        test_name="<suite>",
                        status="timeout",
                        error_message=f"Test execution timed out after {timeout}s",
                    )
                ],
            )
        except Exception as e:
            return ExecutionResult(
                suite_name=test_file.stem,
                test_results=[
                    TestResult(
                        test_name="<suite>",
                        status="error",
                        error_message=str(e),
                    )
                ],
            )

    def _parse_pytest_output(self, stdout: str, stderr: str) -> list[TestResult]:
        """Parse pytest verbose output into TestResult objects."""
        results = []
        seen_names = set()
        import re

        # Extract failure details from FAILURES section
        failure_details: dict[str, str] = {}
        failure_block = re.split(r"={3,}\s*FAILURES\s*={3,}", stdout)
        if len(failure_block) > 1:
            for match in re.finditer(
                r"_{3,}\s*(\w+)\s*_{3,}\n(.*?)(?=_{3,}|\Z)",
                failure_block[1],
                re.DOTALL,
            ):
                failure_details[match.group(1)] = match.group(2).strip()

        for line in stdout.split("\n"):
            line = line.strip()

            # Match pytest verbose output: path::test_name PASSED/FAILED [percentage]
            match = re.match(
                r".*?::(\w+)\s+(PASSED|FAILED|ERROR|SKIPPED)\s*(\[.*\])?",
                line,
            )
            if match:
                name = match.group(1)
                status_str = match.group(2).lower()

                if name not in seen_names:
                    seen_names.add(name)
                    error_msg = failure_details.get(name, "")
                    results.append(
                        TestResult(
                            test_name=name,
                            status=status_str,
                            error_message=error_msg if status_str == "failed" else "",
                            stdout=stdout,
                            stderr=stderr,
                        )
                    )

        # If no individual tests parsed, fall back to summary parsing
        if not results:
            # Try short summary: FAILED path::test_name - reason
            for line in stdout.split("\n"):
                match = re.match(
                    r"FAILED\s+.*?::(\w+)", line.strip()
                )
                if match:
                    name = match.group(1)
                    if name not in seen_names:
                        seen_names.add(name)
                        results.append(
                            TestResult(
                                test_name=name,
                                status="failed",
                                stdout=stdout,
                                stderr=stderr,
                            )
                        )

        # Last resort: create a single result from overall output
        if not results:
            has_failures = "FAILED" in stdout or "ERROR" in stdout
            results.append(
                TestResult(
                    test_name="<suite>",
                    status="failed" if has_failures else "passed",
                    stdout=stdout,
                    stderr=stderr,
                )
            )

        return results
