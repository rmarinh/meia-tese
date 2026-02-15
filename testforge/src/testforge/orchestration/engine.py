"""Main workflow engine — unified entry point for all pipelines."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from testforge.orchestration.golden_pipeline import (
    GoldenPipelineConfig,
    GoldenPipelineResult,
    run_golden_pipeline,
)
from testforge.orchestration.observer_pipeline import (
    ObserverPipelineConfig,
    ObserverPipelineResult,
    run_observer_pipeline,
)

logger = logging.getLogger("testforge.orchestration.engine")


class PipelineRequest(BaseModel):
    """Unified request for any pipeline."""

    mode: str  # "golden", "observer", "combined"

    # Golden mode inputs
    golden_file_paths: list[str] = []
    golden_source_codes: list[str] = []

    # Observer mode inputs
    captured_exchanges: list[dict[str, Any]] = []
    har_file_path: str | None = None

    # Common config
    app_name: str = "app"
    base_url: str = "http://localhost:5000"
    app_description: str = ""
    num_tests: int = 10
    execute_tests: bool = True
    working_dir: str | None = None


class PipelineResponse(BaseModel):
    """Unified response from any pipeline."""

    mode: str
    success: bool
    golden_result: dict[str, Any] | None = None
    observer_result: dict[str, Any] | None = None
    errors: list[str] = []
    test_file_path: str = ""
    summary: str = ""


async def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    """Run the requested pipeline(s)."""
    if request.mode == "golden":
        return await _run_golden(request)
    elif request.mode == "observer":
        return await _run_observer(request)
    elif request.mode == "combined":
        return await _run_combined(request)
    else:
        return PipelineResponse(
            mode=request.mode,
            success=False,
            errors=[f"Unknown mode: {request.mode}"],
        )


async def _run_golden(request: PipelineRequest) -> PipelineResponse:
    config = GoldenPipelineConfig(
        base_url=request.base_url,
        app_description=request.app_description,
        num_tests=request.num_tests,
        execute_tests=request.execute_tests,
        working_dir=request.working_dir,
    )

    result = await run_golden_pipeline(
        golden_file_paths=request.golden_file_paths,
        golden_source_codes=request.golden_source_codes,
        config=config,
    )

    summary = ""
    if result.validation_result:
        summary = result.validation_result.summary

    return PipelineResponse(
        mode="golden",
        success=result.success,
        golden_result={
            "test_count": result.test_suite.test_count if result.test_suite else 0,
            "raw_response": result.raw_llm_response,
            "test_file": result.test_suite.to_file_content() if result.test_suite else "",
        },
        errors=result.errors,
        test_file_path=result.test_file_path,
        summary=summary,
    )


async def _run_observer(request: PipelineRequest) -> PipelineResponse:
    config = ObserverPipelineConfig(
        app_name=request.app_name,
        base_url=request.base_url,
        app_description=request.app_description,
        num_tests=request.num_tests,
        execute_tests=request.execute_tests,
        working_dir=request.working_dir,
    )

    result = await run_observer_pipeline(
        captured_exchanges=request.captured_exchanges,
        har_file_path=request.har_file_path,
        config=config,
    )

    summary = ""
    if result.validation_result:
        summary = result.validation_result.summary

    return PipelineResponse(
        mode="observer",
        success=result.success,
        observer_result={
            "endpoint_count": result.endpoint_map.endpoint_count if result.endpoint_map else 0,
            "test_count": result.test_suite.test_count if result.test_suite else 0,
            "raw_response": result.raw_llm_response,
            "test_file": result.test_suite.to_file_content() if result.test_suite else "",
        },
        errors=result.errors,
        test_file_path=result.test_file_path,
        summary=summary,
    )


async def _run_combined(request: PipelineRequest) -> PipelineResponse:
    """Run golden first (for style guide), then observer with that style."""
    # Step 1: Analyze golden examples for style
    from testforge.agents.analyzer.pattern_extractor import AnalyzerAgent, AnalyzerInput

    style_guide = None
    if request.golden_file_paths or request.golden_source_codes:
        analyzer = AnalyzerAgent()
        analyzer_output = await analyzer.run(
            AnalyzerInput(
                golden_file_paths=request.golden_file_paths,
                golden_source_codes=request.golden_source_codes,
            )
        )
        style_guide = analyzer_output.style_guide

    # Step 2: Run observer pipeline with golden style
    config = ObserverPipelineConfig(
        app_name=request.app_name,
        base_url=request.base_url,
        app_description=request.app_description,
        num_tests=request.num_tests,
        execute_tests=request.execute_tests,
        working_dir=request.working_dir,
        golden_style_guide=style_guide,
    )

    result = await run_observer_pipeline(
        captured_exchanges=request.captured_exchanges,
        har_file_path=request.har_file_path,
        config=config,
    )

    summary = ""
    if result.validation_result:
        summary = result.validation_result.summary

    return PipelineResponse(
        mode="combined",
        success=result.success,
        observer_result={
            "endpoint_count": result.endpoint_map.endpoint_count if result.endpoint_map else 0,
            "test_count": result.test_suite.test_count if result.test_suite else 0,
            "test_file": result.test_suite.to_file_content() if result.test_suite else "",
        },
        errors=result.errors,
        test_file_path=result.test_file_path,
        summary=summary,
    )
