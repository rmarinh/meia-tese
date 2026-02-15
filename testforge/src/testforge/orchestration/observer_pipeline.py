"""Observer Pipeline — Observer → Mapper → Generator → Executor → Validator."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from testforge.agents.executor.runner import ExecutorAgent, ExecutorInput
from testforge.agents.generator.api_test_gen import GeneratorAgent, GeneratorInput
from testforge.agents.mapper.api_mapper import MapperAgent, MapperInput
from testforge.agents.observer.http_proxy import ObserverAgent, ObserverInput
from testforge.agents.validator.quality import ValidatorAgent, ValidatorInput
from testforge.models.results import ValidationResult
from testforge.models.style_guide import TestStyleGuide
from testforge.models.test_model import EndpointMap, TestSuite

logger = logging.getLogger("testforge.orchestration.observer")


@dataclass
class ObserverPipelineConfig:
    """Configuration for the Observer pipeline."""

    app_name: str = "app"
    base_url: str = "http://localhost:5000"
    app_description: str = ""
    num_tests: int = 10
    execute_tests: bool = True
    working_dir: str | None = None
    proxy_port: int = 8080
    # Optional: combine with golden examples
    golden_style_guide: TestStyleGuide | None = None


@dataclass
class ObserverPipelineResult:
    """Result from an Observer pipeline run."""

    endpoint_map: EndpointMap | None = None
    test_suite: TestSuite | None = None
    validation_result: ValidationResult | None = None
    raw_llm_response: str = ""
    test_file_path: str = ""
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return bool(self.test_suite) and not self.errors


async def run_observer_pipeline(
    captured_exchanges: list[dict[str, Any]] = [],
    har_file_path: str | None = None,
    config: ObserverPipelineConfig | None = None,
) -> ObserverPipelineResult:
    """Run the complete Observer pipeline.

    Flow: Observer → Mapper → Generator → Executor → Validator
    """
    config = config or ObserverPipelineConfig()
    result = ObserverPipelineResult()

    # Step 1: Capture/import traffic
    logger.info("Step 1/5: Capturing HTTP traffic...")
    observer = ObserverAgent()
    try:
        observer_output = await observer.run(
            ObserverInput(
                app_name=config.app_name,
                base_url=config.base_url,
                proxy_port=config.proxy_port,
                captured_exchanges=captured_exchanges,
                har_file_path=har_file_path,
            )
        )
        record = observer_output.interaction_record
        logger.info("Captured %d exchanges", len(record.http_exchanges))
    except Exception as e:
        result.errors.append(f"Observer failed: {e}")
        logger.exception("Observer failed")
        return result

    if not record.http_exchanges:
        result.errors.append("No HTTP exchanges captured")
        return result

    # Step 2: Map traffic to endpoints
    logger.info("Step 2/5: Mapping endpoints...")
    mapper = MapperAgent()
    try:
        mapper_output = await mapper.run(MapperInput(interaction_record=record))
        result.endpoint_map = mapper_output.endpoint_map
        logger.info("Mapped %d endpoints", result.endpoint_map.endpoint_count)
    except Exception as e:
        result.errors.append(f"Mapper failed: {e}")
        logger.exception("Mapper failed")
        return result

    # Step 3: Generate tests
    logger.info("Step 3/5: Generating tests...")
    generator = GeneratorAgent()

    # Build a minimal style guide if none provided
    style_guide = config.golden_style_guide
    if not style_guide:
        style_guide = TestStyleGuide(
            framework="pytest",
            http_client="requests",
        )

    try:
        generator_output = await generator.run(
            GeneratorInput(
                style_guide=style_guide,
                golden_examples=style_guide.golden_examples,
                endpoint_map=result.endpoint_map,
                app_description=config.app_description or config.app_name,
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

    # Step 4: Execute tests (optional)
    execution_result = None
    if config.execute_tests:
        logger.info("Step 4/5: Executing tests...")
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
            result.test_file_path = executor_output.test_file_path
            logger.info(
                "Execution: %d passed, %d failed",
                execution_result.passed,
                execution_result.failed,
            )
        except Exception as e:
            result.errors.append(f"Executor failed: {e}")
            logger.exception("Executor failed")
    else:
        logger.info("Step 4/5: Skipping test execution")

    # Step 5: Validate
    logger.info("Step 5/5: Validating tests...")
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
