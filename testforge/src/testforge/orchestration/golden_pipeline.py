"""Golden Examples Pipeline — Analyzer → Generator → Executor → Validator."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from testforge.agents.analyzer.pattern_extractor import AnalyzerAgent, AnalyzerInput
from testforge.agents.executor.runner import ExecutorAgent, ExecutorInput
from testforge.agents.generator.api_test_gen import GeneratorAgent, GeneratorInput
from testforge.agents.validator.quality import ValidatorAgent, ValidatorInput
from testforge.models.results import ExecutionResult, ValidationResult
from testforge.models.style_guide import TestStyleGuide
from testforge.models.test_model import EndpointMap, TestSuite

logger = logging.getLogger("testforge.orchestration.golden")


@dataclass
class GoldenPipelineConfig:
    """Configuration for the Golden Examples pipeline."""

    base_url: str = "http://localhost:5000"
    app_description: str = ""
    num_tests: int = 10
    execute_tests: bool = True
    working_dir: str | None = None
    endpoint_map: EndpointMap | None = None


@dataclass
class GoldenPipelineResult:
    """Result from a Golden Examples pipeline run."""

    style_guide: TestStyleGuide | None = None
    test_suite: TestSuite | None = None
    execution_result: ExecutionResult | None = None
    validation_result: ValidationResult | None = None
    raw_llm_response: str = ""
    test_file_path: str = ""
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return bool(self.test_suite) and not self.errors


async def run_golden_pipeline(
    golden_file_paths: list[str] = [],
    golden_source_codes: list[str] = [],
    config: GoldenPipelineConfig | None = None,
) -> GoldenPipelineResult:
    """Run the complete Golden Examples pipeline.

    Flow: Analyzer → Generator → Executor → Validator
    """
    config = config or GoldenPipelineConfig()
    result = GoldenPipelineResult()

    # Step 1: Analyze golden examples
    logger.info("Step 1/4: Analyzing golden examples...")
    analyzer = AnalyzerAgent()
    try:
        analyzer_output = await analyzer.run(
            AnalyzerInput(
                golden_file_paths=golden_file_paths,
                golden_source_codes=golden_source_codes,
            )
        )
        result.style_guide = analyzer_output.style_guide
        logger.info(
            "Analyzed %d golden examples, found %d test patterns",
            len(analyzer_output.golden_examples),
            sum(len(ex.test_functions) for ex in analyzer_output.golden_examples),
        )
    except Exception as e:
        result.errors.append(f"Analyzer failed: {e}")
        logger.exception("Analyzer failed")
        return result

    # Step 2: Generate new tests
    logger.info("Step 2/4: Generating tests...")
    generator = GeneratorAgent()
    try:
        generator_output = await generator.run(
            GeneratorInput(
                style_guide=analyzer_output.style_guide,
                golden_examples=analyzer_output.golden_examples,
                endpoint_map=config.endpoint_map,
                app_description=config.app_description,
                base_url=config.base_url,
                num_tests=config.num_tests,
            )
        )
        result.test_suite = generator_output.test_suite
        result.raw_llm_response = generator_output.raw_llm_response
        logger.info("Generated %d tests", generator_output.test_suite.test_count)
    except Exception as e:
        result.errors.append(f"Generator failed: {e}")
        logger.exception("Generator failed")
        return result

    # Step 3: Execute tests (optional)
    execution_result = None
    if config.execute_tests:
        logger.info("Step 3/4: Executing tests...")
        executor = ExecutorAgent()
        try:
            executor_output = await executor.run(
                ExecutorInput(
                    test_suite=result.test_suite,
                    base_url=config.base_url,
                    working_dir=config.working_dir,
                )
            )
            execution_result = executor_output.execution_result
            result.execution_result = execution_result
            result.test_file_path = executor_output.test_file_path
            logger.info(
                "Execution: %d passed, %d failed out of %d",
                execution_result.passed,
                execution_result.failed,
                len(execution_result.test_results),
            )
        except Exception as e:
            result.errors.append(f"Executor failed: {e}")
            logger.exception("Executor failed")
    else:
        logger.info("Step 3/4: Skipping test execution")

    # Step 4: Validate
    logger.info("Step 4/4: Validating tests...")
    validator = ValidatorAgent()
    try:
        validator_output = await validator.run(
            ValidatorInput(
                test_suite=result.test_suite,
                execution_result=execution_result,
            )
        )
        result.validation_result = validator_output.validation_result
        logger.info("Validation: %s", result.validation_result.summary)
    except Exception as e:
        result.errors.append(f"Validator failed: {e}")
        logger.exception("Validator failed")

    return result
