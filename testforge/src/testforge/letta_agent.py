"""Letta-powered TestForge agent with persistent memory and custom tools.

This module creates a Letta agent that can:
- Learn about target applications via conversation
- Analyze golden test examples
- Generate insightful tests
- Execute tests and report results
- Remember everything across sessions (persistent archival + core memory)
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from letta_client import Letta

logger = logging.getLogger("testforge.letta_agent")

LETTA_BASE_URL = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
LLM_MODEL = os.environ.get("TESTFORGE_LETTA_MODEL", "ollama/llama3.1:8b")
EMBEDDING_MODEL = os.environ.get("TESTFORGE_LETTA_EMBEDDING", "ollama/mxbai-embed-large:latest")

# ─── Tool Functions ───────────────────────────────────────────────────
# These get registered with Letta and run inside the agent's tool sandbox.
# They must be self-contained (imports inside the function body).


def analyze_golden_tests(file_paths_json: str) -> str:
    """Analyze golden test files to extract patterns, conventions, and style.

    Args:
        file_paths_json (str): JSON array of file paths to golden test files, e.g. '["tests/test_api.py"]'

    Returns:
        str: JSON summary of extracted patterns including framework, HTTP client, fixtures, and test function patterns.
    """
    import json as _json
    import sys as _sys

    _sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

    from testforge.agents.analyzer.ast_analyzer import parse_golden_files

    paths = _json.loads(file_paths_json)
    examples = parse_golden_files(paths)

    if not examples:
        return _json.dumps({"error": "No valid Python test files found", "paths": paths})

    results = []
    for ex in examples:
        results.append({
            "file": ex.file_path,
            "imports": len(ex.imports),
            "fixtures": [f.name for f in ex.fixtures],
            "test_functions": [
                {
                    "name": f.name,
                    "http_method": f.http_method,
                    "endpoint": f.endpoint,
                    "assertions": len(f.assertions),
                    "docstring": f.docstring,
                }
                for f in ex.test_functions
            ],
            "helpers": ex.helper_functions,
            "classes": ex.class_names,
        })

    return _json.dumps({
        "total_files": len(examples),
        "total_tests": sum(len(ex.test_functions) for ex in examples),
        "examples": results,
    }, indent=2)


def generate_tests_from_golden(
    golden_file_paths_json: str,
    base_url: str,
    app_description: str,
    num_tests: int,
) -> str:
    """Generate new API tests based on golden example files using the full pipeline.

    Args:
        golden_file_paths_json (str): JSON array of paths to golden test files.
        base_url (str): Base URL of the target application, e.g. 'http://localhost:5000'.
        app_description (str): Brief description of what the application does.
        num_tests (int): Number of test functions to generate.

    Returns:
        str: JSON with generated test code, quality scores, and validation summary.
    """
    import asyncio
    import json as _json
    import sys as _sys

    _sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

    from testforge.orchestration.golden_pipeline import (
        GoldenPipelineConfig,
        run_golden_pipeline,
    )

    paths = _json.loads(golden_file_paths_json)
    config = GoldenPipelineConfig(
        base_url=base_url,
        app_description=app_description,
        num_tests=int(num_tests),
        execute_tests=False,
    )

    result = asyncio.run(run_golden_pipeline(golden_file_paths=paths, config=config))

    if not result.success:
        return _json.dumps({"error": "Pipeline failed", "errors": result.errors})

    test_code = result.test_suite.to_file_content() if result.test_suite else ""
    quality = []
    if result.validation_result:
        quality = [
            {"name": qs.test_name, "score": qs.overall_score, "issues": qs.issues}
            for qs in result.validation_result.quality_scores
        ]

    return _json.dumps({
        "success": True,
        "test_count": result.test_suite.test_count if result.test_suite else 0,
        "test_code": test_code,
        "quality_scores": quality,
        "summary": result.validation_result.summary if result.validation_result else "",
    }, indent=2)


def generate_tests_from_endpoints(
    endpoints_json: str,
    base_url: str,
    app_description: str,
    num_tests: int,
) -> str:
    """Generate API tests from endpoint definitions (observer mode).

    Args:
        endpoints_json (str): JSON array of endpoint objects with method, path, description, request_schema, response_schema.
        base_url (str): Base URL of the target application.
        app_description (str): Brief description of what the application does.
        num_tests (int): Number of test functions to generate.

    Returns:
        str: JSON with generated test code and quality assessment.
    """
    import asyncio
    import json as _json
    import sys as _sys

    _sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

    from testforge.orchestration.observer_pipeline import (
        ObserverPipelineConfig,
        run_observer_pipeline,
    )

    endpoints = _json.loads(endpoints_json)

    # Convert endpoint definitions to captured exchange format
    exchanges = []
    for ep in endpoints:
        exchanges.append({
            "method": ep.get("method", "GET"),
            "url": f"{base_url}{ep.get('path', '/')}",
            "path": ep.get("path", "/"),
            "status_code": 200,
            "request_body": ep.get("sample_request"),
            "request_content_type": "application/json" if ep.get("sample_request") else None,
            "response_body": ep.get("sample_response", {}),
            "response_content_type": "application/json",
        })

    config = ObserverPipelineConfig(
        app_name=app_description or "app",
        base_url=base_url,
        app_description=app_description,
        num_tests=int(num_tests),
        execute_tests=False,
    )

    result = asyncio.run(run_observer_pipeline(captured_exchanges=exchanges, config=config))

    if not result.success:
        return _json.dumps({"error": "Pipeline failed", "errors": result.errors})

    test_code = result.test_suite.to_file_content() if result.test_suite else ""
    return _json.dumps({
        "success": True,
        "test_count": result.test_suite.test_count if result.test_suite else 0,
        "endpoints_mapped": result.endpoint_map.endpoint_count if result.endpoint_map else 0,
        "test_code": test_code,
        "summary": result.validation_result.summary if result.validation_result else "",
    }, indent=2)


def run_tests(test_file_path: str, base_url: str) -> str:
    """Execute a generated test file using pytest and return results.

    Args:
        test_file_path (str): Path to the test file to execute.
        base_url (str): Base URL of the running application under test.

    Returns:
        str: JSON with test results including pass/fail status for each test.
    """
    import json as _json
    import subprocess

    env = {**__import__("os").environ, "BASE_URL": base_url, "TESTFORGE_RUN": "1"}

    try:
        proc = subprocess.run(
            ["python", "-m", "pytest", test_file_path, "-v", "--tb=short", "--no-header"],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )

        return _json.dumps({
            "exit_code": proc.returncode,
            "passed": proc.returncode == 0,
            "stdout": proc.stdout[-3000:] if len(proc.stdout) > 3000 else proc.stdout,
            "stderr": proc.stderr[-1000:] if len(proc.stderr) > 1000 else proc.stderr,
        }, indent=2)
    except subprocess.TimeoutExpired:
        return _json.dumps({"error": "Test execution timed out after 120s"})
    except Exception as e:
        return _json.dumps({"error": str(e)})


def save_test_file(test_code: str, output_path: str) -> str:
    """Save generated test code to a file.

    Args:
        test_code (str): The Python test code to save.
        output_path (str): Path where the test file should be saved.

    Returns:
        str: Confirmation message with the saved file path.
    """
    from pathlib import Path as _Path

    path = _Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(test_code, encoding="utf-8")
    return f"Test file saved to: {output_path} ({len(test_code)} characters)"


def list_files(directory: str, pattern: str) -> str:
    """List files in a directory matching a glob pattern.

    Args:
        directory (str): Directory path to search in.
        pattern (str): Glob pattern like '*.py' or 'test_*.py'.

    Returns:
        str: JSON array of matching file paths.
    """
    import json as _json
    from pathlib import Path as _Path

    path = _Path(directory)
    if not path.exists():
        return _json.dumps({"error": f"Directory not found: {directory}"})

    files = sorted(str(f) for f in path.glob(pattern))
    return _json.dumps(files)


def read_file(file_path: str) -> str:
    """Read the contents of a file.

    Args:
        file_path (str): Path to the file to read.

    Returns:
        str: The file contents (truncated to 8000 chars if too large).
    """
    from pathlib import Path as _Path

    path = _Path(file_path)
    if not path.exists():
        return f"Error: File not found: {file_path}"

    content = path.read_text(encoding="utf-8")
    if len(content) > 8000:
        return content[:8000] + f"\n\n... (truncated, {len(content)} total characters)"
    return content


# ─── Agent Setup ──────────────────────────────────────────────────────

PERSONA_MEMORY = """\
I am TestForge, an AI-powered test generation assistant. I specialize in:
- Analyzing existing test suites to learn patterns and conventions
- Generating high-quality, insightful API and integration tests
- Understanding REST APIs by analyzing endpoints, schemas, and behaviors
- Running tests and interpreting results
- Progressively learning about applications to generate better tests over time

I generate tests that find real bugs — not trivial smoke tests. I think about:
state integrity, boundary values, business logic, error quality, security, and data consistency.

Current state: No application loaded yet. Waiting for the user to describe their application or provide golden test examples.\
"""

HUMAN_MEMORY = """\
The user is a software developer who wants to automatically generate tests for their application. \
They may provide golden test examples, describe API endpoints, or ask me to analyze existing code. \
I should ask clarifying questions about the application when needed.\
"""

APP_CONTEXT_MEMORY = """\
No application loaded yet. When the user provides information about their app, I will record:
- Application name and base URL
- Discovered endpoints (method, path, schema)
- Test patterns learned from golden examples
- Coverage status: which endpoints have been tested
- Quality notes: what kinds of tests work well for this app\
"""


def _make_client(base_url: str | None = None) -> Letta:
    """Create a Letta client with generous timeouts for local LLM inference."""
    import httpx

    return Letta(
        base_url=base_url or LETTA_BASE_URL,
        timeout=httpx.Timeout(300.0, connect=30.0),  # 5 min for local LLM
    )


def get_or_create_agent(
    client: Letta | None = None,
    agent_name: str = "testforge",
    llm_model: str | None = None,
    embedding_model: str | None = None,
) -> tuple[Letta, str]:
    """Get an existing TestForge agent or create a new one.

    Returns (client, agent_id).
    """
    if client is None:
        client = _make_client()

    model = llm_model or LLM_MODEL
    embedding = embedding_model or EMBEDDING_MODEL

    # Check if agent already exists
    agents = client.agents.list()
    for agent in agents:
        if agent.name == agent_name:
            logger.info("Found existing agent: %s (%s)", agent.name, agent.id)
            return client, agent.id

    # Register tools
    tool_funcs = [
        analyze_golden_tests,
        generate_tests_from_golden,
        generate_tests_from_endpoints,
        run_tests,
        save_test_file,
        list_files,
        read_file,
    ]

    tool_ids = []
    for func in tool_funcs:
        tool = client.tools.upsert_from_function(func=func)
        tool_ids.append(tool.id)
        logger.info("Registered tool: %s (%s)", func.__name__, tool.id)

    # Create agent
    agent = client.agents.create(
        name=agent_name,
        model=model,
        embedding=embedding,
        context_window_limit=16000,
        memory_blocks=[
            {"label": "persona", "value": PERSONA_MEMORY},
            {"label": "human", "value": HUMAN_MEMORY},
            {"label": "app_context", "value": APP_CONTEXT_MEMORY},
        ],
        tool_ids=tool_ids,
        description="TestForge — Automated test generation assistant with persistent memory",
    )

    logger.info("Created new agent: %s (%s)", agent.name, agent.id)

    # Seed archival memory with testing knowledge
    knowledge_entries = [
        (
            "pytest fixtures: Use @pytest.fixture for reusable setup. Scope options: function, class, "
            "module, session. Fixtures can yield for setup/teardown. Use conftest.py for shared fixtures."
        ),
        (
            "API test patterns: Always test happy path (valid input, expected response), error cases "
            "(invalid input, missing fields, wrong types), edge cases (empty data, boundary values, "
            "special characters), and state consistency (create-read-update-delete chains)."
        ),
        (
            "Insightful test categories: 1) State integrity (CRUD round-trips), 2) Boundary probing "
            "(max lengths, Unicode, SQL injection strings), 3) Business logic (duplicate detection, "
            "constraint violations), 4) Error quality (helpful error messages), 5) Idempotency "
            "(same request twice), 6) Data leakage (responses don't expose sensitive fields)."
        ),
        (
            "Golden example analysis: Use Tree-sitter AST parsing to extract imports, fixtures, test "
            "functions, assertion patterns, HTTP methods, endpoints, decorators, and naming conventions "
            "from existing test files. Build a TestStyleGuide from aggregated patterns."
        ),
    ]

    for entry in knowledge_entries:
        client.agents.passages.create(agent_id=agent.id, text=entry)

    logger.info("Seeded archival memory with %d knowledge entries", len(knowledge_entries))

    return client, agent.id


def chat(
    message: str,
    agent_name: str = "testforge",
    client: Letta | None = None,
) -> str:
    """Send a message to the TestForge agent and get a response.

    Returns the agent's text response.
    """
    client, agent_id = get_or_create_agent(client=client, agent_name=agent_name)

    response = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": message}],
    )

    # Extract text responses from LettaResponse
    texts = []
    tool_calls = []
    for msg in response.messages:
        msg_type = type(msg).__name__
        if msg_type == "AssistantMessage" and hasattr(msg, "content") and msg.content:
            texts.append(msg.content)
        elif msg_type == "ToolCallMessage" and hasattr(msg, "tool_call"):
            tool_calls.append(f"[tool: {msg.tool_call.name}]")
        elif msg_type == "ReasoningMessage" and hasattr(msg, "reasoning"):
            pass  # Skip internal reasoning

    return "\n".join(texts) if texts else "(No text response from agent)"


# ─── CLI Interface ────────────────────────────────────────────────────

def interactive_chat(agent_name: str = "testforge"):
    """Run an interactive chat session with the TestForge agent."""
    from rich.console import Console
    from rich.markdown import Markdown

    console = Console()
    console.print("[bold]TestForge[/bold] — Interactive Test Generation Agent")
    console.print(f"Connected to Letta at {LETTA_BASE_URL}")
    console.print("Type 'quit' to exit, 'reset' to create a new agent\n")

    client = _make_client()

    while True:
        try:
            user_input = input("You> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "reset":
            # Delete existing agent and create fresh
            agents = client.agents.list()
            for agent in agents:
                if agent.name == agent_name:
                    client.agents.delete(agent_id=agent.id)
                    console.print(f"[yellow]Deleted agent {agent.name}[/yellow]")
            console.print("[green]Agent will be recreated on next message[/green]")
            continue

        console.print("[dim]Thinking...[/dim]")

        try:
            response = chat(user_input, agent_name=agent_name, client=client)
            console.print(Markdown(response))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    interactive_chat()
