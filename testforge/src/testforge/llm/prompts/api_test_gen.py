"""Prompt templates for API test generation."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are a senior QA engineer and security tester. You write pytest tests that find \
real bugs — not trivial smoke tests. You think like an attacker and a pedantic user simultaneously.

Your tests should be INSIGHTFUL: they should probe the application's behavior in ways \
that reveal logic errors, race conditions, data integrity issues, and security flaws.

Rules:
- Output ONLY valid Python code, no markdown fences, no explanations
- Follow the exact import style, naming conventions, and assertion patterns from the golden examples
- Each test function must be independent and self-contained
- Use descriptive test names that explain the SCENARIO being tested, not just the endpoint
- Assertions must verify MEANINGFUL properties — not just "status 200", but also:
  - Data consistency (create→read returns same data)
  - State transitions (deleting removes from list, updating changes only targeted fields)
  - Error message quality (useful error messages, not generic 500s)
  - Idempotency (same request twice = same result or appropriate error)
  - Ordering and pagination behavior
  - Concurrent/conflicting operations

Categories of insightful tests to generate:
1. STATE INTEGRITY: Create→Read→Update→Read→Delete→Read chains that verify data consistency
2. BOUNDARY PROBING: Max lengths, zero values, negative IDs, Unicode, SQL injection strings, XSS payloads
3. BUSINESS LOGIC: Duplicate detection, constraint violations, cascading effects
4. ERROR QUALITY: Invalid requests return helpful error messages with correct HTTP codes
5. CONCURRENCY HINTS: What happens when you modify a resource that was just deleted?
6. AUTH BOUNDARIES: Accessing resources that belong to other users, escalation attempts
7. DATA LEAKAGE: Responses don't include fields they shouldn't (passwords, tokens, internal IDs)
8. REGRESSION TRAPS: Tests that would catch common mistakes like off-by-one, null handling, type coercion
"""

GOLDEN_EXAMPLES_TEMPLATE = """\
## Golden Test Examples

These are reference test files that show the coding style, patterns, and conventions to follow. \
Match their style exactly, but generate tests that are MORE thorough and insightful:

{examples}
"""

GENERATION_PROMPT_TEMPLATE = """\
{style_context}

## Target Application

- Base URL: {base_url}
- Application description: {app_description}

## Endpoint Map

{endpoint_info}

## Task

Generate {num_tests} INSIGHTFUL pytest test functions for the endpoints listed above. \
Follow the golden examples' style but write tests that a senior QA engineer would write — \
tests that find real bugs, not just verify happy paths.

For each endpoint, think about:
- What invariants should hold? (e.g., GET after POST returns same data)
- What happens at the boundaries? (empty strings, max length, special chars)
- What state transitions could break? (delete then update, create duplicate)
- What security assumptions could be wrong? (accessing others' data, injection)
- What data integrity guarantees exist? (partial updates preserve other fields)

Output the complete test file including all necessary imports, fixtures, and test functions.
"""

GENERATION_FROM_EXAMPLES_PROMPT = """\
{style_context}

{context_section}

## Task

Based on the golden test examples above, generate {num_tests} new test functions \
that test DIFFERENT and MORE INSIGHTFUL scenarios for the same API.

Do NOT duplicate any existing tests. Think about what a senior QA engineer would test next:

1. DATA ROUND-TRIP: Create a resource, read it back, verify every field matches
2. PARTIAL UPDATE SAFETY: Update one field, verify other fields unchanged
3. DELETE CONSISTENCY: Delete a resource, verify it's gone from both GET and LIST
4. DUPLICATE HANDLING: Try creating the same resource twice, verify correct error
5. BOUNDARY VALUES: Empty strings, very long strings, special characters (unicode, emoji, SQL chars)
6. TYPE CONFUSION: Send wrong types (string where int expected, null for required fields)
7. ORDERING/FILTERING: If list endpoints exist, test search/filter/sort behavior
8. ERROR MESSAGE QUALITY: Verify error responses have useful messages, not just status codes
9. IDEMPOTENCY: Same DELETE twice — first succeeds, second returns 404
10. CROSS-ENDPOINT CONSISTENCY: Data from list endpoint matches individual get endpoint

Output ONLY the new test functions (no imports or fixtures — those will be prepended from the examples). \
Each function should start with 'def test_'.
"""

CONTEXT_SECTION_TEMPLATE = """\
## Application Context

This application has been analyzed before. Here's what we know:
- Previously tested endpoints: {tested_endpoints}
- Untested endpoints: {untested_endpoints}
- Known coverage gaps: {coverage_gaps}
- Previous test names (do NOT regenerate): {known_test_names}

Focus on untested endpoints and coverage gaps first.
"""


def build_style_context(golden_sources: list[str]) -> str:
    """Build the style context section from golden example source code."""
    example_blocks = []
    for i, source in enumerate(golden_sources, 1):
        example_blocks.append(f"### Example {i}\n\n```python\n{source}\n```")
    return GOLDEN_EXAMPLES_TEMPLATE.format(examples="\n\n".join(example_blocks))


def build_context_section(
    tested_endpoints: list[str] | None = None,
    untested_endpoints: list[str] | None = None,
    coverage_gaps: list[str] | None = None,
    known_test_names: list[str] | None = None,
) -> str:
    """Build the application context section for progressive learning."""
    if not any([tested_endpoints, untested_endpoints, coverage_gaps]):
        return ""
    return CONTEXT_SECTION_TEMPLATE.format(
        tested_endpoints=", ".join(tested_endpoints or ["none"]),
        untested_endpoints=", ".join(untested_endpoints or ["none"]),
        coverage_gaps=", ".join(coverage_gaps or ["none"]),
        known_test_names=", ".join(known_test_names[-20:] if known_test_names else ["none"]),
    )


def build_endpoint_info(endpoints: list[dict]) -> str:
    """Format endpoint information for the prompt."""
    lines = []
    for ep in endpoints:
        method = ep.get("method", "GET")
        path = ep.get("path", "/")
        desc = ep.get("description", "")
        lines.append(f"- {method} {path}: {desc}")
        if ep.get("request_schema"):
            lines.append(f"  Request body schema: {ep['request_schema']}")
        if ep.get("response_schema"):
            lines.append(f"  Response schema: {ep['response_schema']}")
        if ep.get("sample_request"):
            lines.append(f"  Sample request: {ep['sample_request']}")
        if ep.get("sample_response"):
            lines.append(f"  Sample response: {ep['sample_response']}")
        if ep.get("query_params"):
            lines.append(f"  Query params: {ep['query_params']}")
        if ep.get("observed_status_codes"):
            lines.append(f"  Observed status codes: {ep['observed_status_codes']}")
        if ep.get("auth_required"):
            lines.append(f"  Auth: {ep.get('auth_type', 'required')}")
    return "\n".join(lines) if lines else "No endpoint information available."
