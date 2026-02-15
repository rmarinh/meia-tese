"""Generator Agent — produces API test code using LLM with golden examples."""

from __future__ import annotations

import re
import uuid

from pydantic import BaseModel

from testforge.agents.base import BaseAgent
from testforge.llm import gateway
from testforge.llm.prompts.api_test_gen import (
    GENERATION_FROM_EXAMPLES_PROMPT,
    GENERATION_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
    build_context_section,
    build_endpoint_info,
    build_style_context,
)
from testforge.models.style_guide import GoldenExample, TestStyleGuide
from testforge.models.test_model import EndpointMap, GeneratedTest, TestSuite


class GeneratorInput(BaseModel):
    """Input for the Generator Agent."""

    style_guide: TestStyleGuide
    golden_examples: list[GoldenExample]
    endpoint_map: EndpointMap | None = None
    app_description: str = ""
    base_url: str = "http://localhost:5000"
    num_tests: int = 10

    # Application context for progressive learning
    tested_endpoints: list[str] = []
    untested_endpoints: list[str] = []
    coverage_gaps: list[str] = []
    known_test_names: list[str] = []


class GeneratorOutput(BaseModel):
    """Output of the Generator Agent."""

    test_suite: TestSuite
    raw_llm_response: str = ""


class GeneratorAgent(BaseAgent[GeneratorInput, GeneratorOutput]):
    """Generates API tests using LLM with few-shot prompting from golden examples."""

    def __init__(self):
        super().__init__("GeneratorAgent")

    async def run(self, input_data: GeneratorInput) -> GeneratorOutput:
        golden_sources = [ex.source_code for ex in input_data.golden_examples]
        style_context = build_style_context(golden_sources)

        if input_data.endpoint_map and input_data.endpoint_map.endpoints:
            prompt = self._build_endpoint_prompt(input_data, style_context)
        else:
            prompt = self._build_examples_only_prompt(input_data, style_context)

        raw_response = await gateway.complete(
            prompt=prompt,
            system=SYSTEM_PROMPT,
        )

        test_suite = self._parse_response(raw_response, input_data)

        return GeneratorOutput(
            test_suite=test_suite,
            raw_llm_response=raw_response,
        )

    def _build_endpoint_prompt(self, input_data: GeneratorInput, style_context: str) -> str:
        endpoint_info = build_endpoint_info(
            [ep.model_dump() for ep in input_data.endpoint_map.endpoints]
        )
        return GENERATION_PROMPT_TEMPLATE.format(
            style_context=style_context,
            base_url=input_data.base_url,
            app_description=input_data.app_description or "REST API application",
            endpoint_info=endpoint_info,
            num_tests=input_data.num_tests,
        )

    def _build_examples_only_prompt(self, input_data: GeneratorInput, style_context: str) -> str:
        context_section = build_context_section(
            tested_endpoints=input_data.tested_endpoints or None,
            untested_endpoints=input_data.untested_endpoints or None,
            coverage_gaps=input_data.coverage_gaps or None,
            known_test_names=input_data.known_test_names or None,
        )
        return GENERATION_FROM_EXAMPLES_PROMPT.format(
            style_context=style_context,
            context_section=context_section,
            num_tests=input_data.num_tests,
        )

    def _parse_response(self, raw: str, input_data: GeneratorInput) -> TestSuite:
        """Parse the LLM response into a TestSuite."""
        # Strip markdown code fences if present
        code = raw.strip()
        code = re.sub(r"^```python\s*\n?", "", code)
        code = re.sub(r"\n?```\s*$", "", code)
        code = code.strip()

        # Split into individual test functions
        tests = self._extract_test_functions(code)

        # Extract imports and setup (everything before first test function)
        imports_code, setup_code = self._extract_preamble(code)

        # If no imports found in LLM output, reconstruct from golden examples
        if not imports_code.strip():
            imports_code = self._build_imports_from_style(input_data.style_guide)

        return TestSuite(
            name=f"generated_api_tests_{uuid.uuid4().hex[:8]}",
            description=f"Auto-generated from {len(input_data.golden_examples)} golden examples",
            tests=tests,
            imports_code=imports_code,
            setup_code=setup_code,
            target_app=input_data.app_description,
            base_url=input_data.base_url,
        )

    def _extract_test_functions(self, code: str) -> list[GeneratedTest]:
        """Extract individual test functions from code."""
        tests = []
        # Split on function definitions starting with 'def test_'
        pattern = r"((?:@[\w.]+(?:\(.*?\))?\s*\n)*def test_\w+\(.*?\).*?)(?=\n(?:@[\w.]+|def test_|\Z))"
        matches = re.findall(pattern, code, re.DOTALL)

        if not matches:
            # Fallback: try splitting by 'def test_'
            parts = re.split(r"(?=\ndef test_)", code)
            matches = [p.strip() for p in parts if "def test_" in p]

        for match in matches:
            match = match.strip()
            if not match:
                continue

            name_match = re.search(r"def (test_\w+)", match)
            name = name_match.group(1) if name_match else f"test_generated_{len(tests)}"

            # Detect target endpoint
            endpoint = None
            method = None
            for m in ("get", "post", "put", "patch", "delete"):
                url_match = re.search(rf'\.{m}\s*\(\s*[f"\'](.*?)["\']', match)
                if url_match:
                    method = m.upper()
                    endpoint = url_match.group(1)
                    break

            tests.append(
                GeneratedTest(
                    id=uuid.uuid4().hex[:8],
                    name=name,
                    source_code=match,
                    test_type="api",
                    target_endpoint=endpoint,
                    target_method=method,
                )
            )

        return tests

    def _extract_preamble(self, code: str) -> tuple[str, str]:
        """Extract imports and setup code before the first test function."""
        first_test = re.search(r"(?:@[\w.]+(?:\(.*?\))?\s*\n)*def test_", code)
        if not first_test:
            return "", ""

        preamble = code[: first_test.start()].strip()
        lines = preamble.split("\n")

        imports = []
        setup = []
        in_imports = True

        for line in lines:
            stripped = line.strip()
            if in_imports and (
                stripped.startswith("import ")
                or stripped.startswith("from ")
                or stripped == ""
            ):
                imports.append(line)
            else:
                in_imports = False
                setup.append(line)

        return "\n".join(imports).strip(), "\n".join(setup).strip()

    def _build_imports_from_style(self, style_guide: TestStyleGuide) -> str:
        """Reconstruct imports from style guide if LLM didn't include them."""
        lines = []
        for imp in style_guide.common_imports:
            if imp.is_from_import:
                names = ", ".join(imp.names)
                lines.append(f"from {imp.module} import {names}")
            elif imp.alias:
                lines.append(f"import {imp.module} as {imp.alias}")
            else:
                lines.append(f"import {imp.module}")
        return "\n".join(lines)
