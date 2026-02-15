"""Analyzer Agent — extracts patterns from golden test examples."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from pydantic import BaseModel

from testforge.agents.analyzer.ast_analyzer import parse_golden_files
from testforge.agents.base import BaseAgent
from testforge.models.style_guide import (
    AssertionPattern,
    FixturePattern,
    GoldenExample,
    ImportPattern,
    TestStyleGuide,
)


class AnalyzerInput(BaseModel):
    """Input for the Analyzer Agent."""

    golden_file_paths: list[str] = []
    golden_source_codes: list[str] = []  # alternative: provide code directly


class AnalyzerOutput(BaseModel):
    """Output of the Analyzer Agent."""

    style_guide: TestStyleGuide
    golden_examples: list[GoldenExample]


class AnalyzerAgent(BaseAgent[AnalyzerInput, AnalyzerOutput]):
    """Parses golden test examples and extracts patterns/conventions."""

    def __init__(self):
        super().__init__("AnalyzerAgent")

    async def run(self, input_data: AnalyzerInput) -> AnalyzerOutput:
        examples: list[GoldenExample] = []

        # Parse from file paths
        if input_data.golden_file_paths:
            examples.extend(parse_golden_files(input_data.golden_file_paths))

        # Parse from source code strings
        for i, source in enumerate(input_data.golden_source_codes):
            from testforge.agents.analyzer.ast_analyzer import parse_python_file

            examples.append(parse_python_file(source, f"<uploaded_{i}.py>"))

        if not examples:
            raise ValueError("No golden examples provided or found")

        style_guide = self._build_style_guide(examples)

        return AnalyzerOutput(
            style_guide=style_guide,
            golden_examples=examples,
        )

    def _build_style_guide(self, examples: list[GoldenExample]) -> TestStyleGuide:
        """Aggregate patterns across all golden examples into a style guide."""
        all_imports: list[ImportPattern] = []
        all_fixtures: list[FixturePattern] = []
        all_assertions: list[AssertionPattern] = []
        all_decorators: list[str] = []
        total_assertions = 0
        total_lines = 0
        test_count = 0
        has_docstrings = 0
        has_parametrize = 0
        has_classes = False

        for example in examples:
            all_imports.extend(example.imports)
            all_fixtures.extend(example.fixtures)

            if example.class_names:
                has_classes = True

            for func in example.test_functions:
                test_count += 1
                total_assertions += len(func.assertions)
                total_lines += func.line_count
                all_assertions.extend(func.assertions)
                all_decorators.extend(func.decorators)

                if func.docstring:
                    has_docstrings += 1
                if any("parametrize" in d for d in func.decorators):
                    has_parametrize += 1

        # Detect framework
        framework = "pytest"
        for imp in all_imports:
            if imp.module == "unittest":
                framework = "unittest"
                break

        # Detect HTTP client
        http_client = "requests"
        for imp in all_imports:
            if imp.module == "httpx" or (imp.is_from_import and "httpx" in imp.module):
                http_client = "httpx"
                break
            elif imp.module == "aiohttp" or (imp.is_from_import and "aiohttp" in imp.module):
                http_client = "aiohttp"
                break

        # Check if using a test client (Flask/FastAPI)
        all_source = " ".join(ex.source_code for ex in examples)
        if "test_client" in all_source or "TestClient" in all_source:
            http_client = "test_client"

        # Find common imports (appear in >50% of files)
        import_counter: Counter[str] = Counter()
        for imp in all_imports:
            key = f"{imp.module}:{','.join(imp.names)}" if imp.is_from_import else imp.module
            import_counter[key] += 1

        threshold = max(1, len(examples) // 2)
        common_imports = []
        seen_imports: set[str] = set()
        for imp in all_imports:
            key = f"{imp.module}:{','.join(imp.names)}" if imp.is_from_import else imp.module
            if import_counter[key] >= threshold and key not in seen_imports:
                common_imports.append(imp)
                seen_imports.add(key)

        # Find common fixtures (deduplicate by name)
        fixture_counter: Counter[str] = Counter()
        for fix in all_fixtures:
            fixture_counter[fix.name] += 1

        common_fixtures = []
        seen_fixtures: set[str] = set()
        for fix in all_fixtures:
            if fix.name not in seen_fixtures:
                common_fixtures.append(fix)
                seen_fixtures.add(fix.name)

        # Find common assertion patterns
        assertion_counter: Counter[str] = Counter()
        for a in all_assertions:
            assertion_counter[a.style] += 1

        common_assertions = [
            AssertionPattern(style=style, pattern=style, frequency=count)
            for style, count in assertion_counter.most_common(5)
        ]

        # Common decorators
        dec_counter: Counter[str] = Counter()
        for d in all_decorators:
            dec_counter[d] += 1
        common_decs = [d for d, _ in dec_counter.most_common(5)]

        return TestStyleGuide(
            framework=framework,
            http_client=http_client,
            naming_convention="snake_case",
            class_based=has_classes,
            common_imports=common_imports,
            common_fixtures=common_fixtures,
            common_assertions=common_assertions,
            common_decorators=common_decs,
            avg_assertions_per_test=total_assertions / max(test_count, 1),
            avg_test_lines=total_lines / max(test_count, 1),
            uses_docstrings=has_docstrings > test_count / 2,
            uses_parametrize=has_parametrize > 0,
            golden_examples=examples,
        )
