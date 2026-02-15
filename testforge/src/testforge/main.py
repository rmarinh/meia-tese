"""FastAPI entry point for TestForge."""

from __future__ import annotations

import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from testforge.config import settings
from testforge.orchestration.engine import PipelineRequest, PipelineResponse, run_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("testforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    logger.info("TestForge started — workspace: %s", settings.workspace_dir)
    yield
    logger.info("TestForge shutting down")


app = FastAPI(
    title="TestForge",
    description="Automated test generation using multi-agent systems and LLMs",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/pipeline/run", response_model=PipelineResponse)
async def run_pipeline_endpoint(request: PipelineRequest):
    """Run a test generation pipeline."""
    try:
        result = await run_pipeline(request)
        return result
    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/golden/upload")
async def upload_golden_examples(
    files: list[UploadFile] = File(...),
    base_url: str = Form("http://localhost:5000"),
    app_description: str = Form(""),
    num_tests: int = Form(10),
    execute_tests: bool = Form(False),
):
    """Upload golden test files and run the golden pipeline."""
    source_codes = []
    for f in files:
        content = await f.read()
        source_codes.append(content.decode("utf-8"))

    request = PipelineRequest(
        mode="golden",
        golden_source_codes=source_codes,
        base_url=base_url,
        app_description=app_description,
        num_tests=num_tests,
        execute_tests=execute_tests,
    )

    result = await run_pipeline(request)
    return result


@app.post("/api/observer/import-har")
async def import_har(
    har_file: UploadFile = File(...),
    app_name: str = Form("app"),
    base_url: str = Form("http://localhost:5000"),
    num_tests: int = Form(10),
    execute_tests: bool = Form(False),
):
    """Import a HAR file and run the observer pipeline."""
    import tempfile

    content = await har_file.read()
    with tempfile.NamedTemporaryFile(suffix=".har", delete=False, mode="wb") as f:
        f.write(content)
        har_path = f.name

    request = PipelineRequest(
        mode="observer",
        har_file_path=har_path,
        app_name=app_name,
        base_url=base_url,
        num_tests=num_tests,
        execute_tests=execute_tests,
    )

    result = await run_pipeline(request)
    return result


@app.post("/api/observer/exchanges")
async def submit_exchanges(
    exchanges: list[dict[str, Any]],
    app_name: str = "app",
    base_url: str = "http://localhost:5000",
    num_tests: int = 10,
    execute_tests: bool = False,
):
    """Submit captured HTTP exchanges and run the observer pipeline."""
    request = PipelineRequest(
        mode="observer",
        captured_exchanges=exchanges,
        app_name=app_name,
        base_url=base_url,
        num_tests=num_tests,
        execute_tests=execute_tests,
    )

    result = await run_pipeline(request)
    return result


def cli():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="TestForge — Automated Test Generation")
    subparsers = parser.add_subparsers(dest="command")

    # Server command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default=settings.host)
    serve_parser.add_argument("--port", type=int, default=settings.port)

    # UI command
    ui_parser = subparsers.add_parser("ui", help="Start the Streamlit UI")
    ui_parser.add_argument("--port", type=int, default=settings.streamlit_port)

    # Generate command (CLI-only golden pipeline)
    gen_parser = subparsers.add_parser("generate", help="Generate tests from golden examples")
    gen_parser.add_argument("golden_files", nargs="+", help="Golden test files")
    gen_parser.add_argument("--base-url", default="http://localhost:5000")
    gen_parser.add_argument("--num-tests", type=int, default=10)
    gen_parser.add_argument("--output", "-o", help="Output file path")
    gen_parser.add_argument("--no-execute", action="store_true")

    # Chat command (Letta interactive agent)
    chat_parser = subparsers.add_parser("chat", help="Interactive chat with TestForge agent (Letta)")
    chat_parser.add_argument("--agent-name", default="testforge", help="Letta agent name")

    args = parser.parse_args()

    if args.command == "serve":
        import uvicorn

        uvicorn.run(
            "testforge.main:app",
            host=args.host,
            port=args.port,
            reload=True,
        )
    elif args.command == "ui":
        ui_path = Path(__file__).parent / "ui" / "streamlit_app.py"
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(ui_path), "--server.port", str(args.port)],
        )
    elif args.command == "generate":
        import asyncio

        asyncio.run(_cli_generate(args))
    elif args.command == "chat":
        from testforge.letta_agent import interactive_chat

        interactive_chat(agent_name=args.agent_name)
    else:
        parser.print_help()


async def _cli_generate(args):
    """CLI generate command handler."""
    from testforge.orchestration.golden_pipeline import (
        GoldenPipelineConfig,
        run_golden_pipeline,
    )

    config = GoldenPipelineConfig(
        base_url=args.base_url,
        num_tests=args.num_tests,
        execute_tests=not args.no_execute,
    )

    result = await run_golden_pipeline(
        golden_file_paths=args.golden_files,
        config=config,
    )

    if result.success and result.test_suite:
        content = result.test_suite.to_file_content()
        if args.output:
            Path(args.output).write_text(content, encoding="utf-8")
            print(f"Generated tests written to: {args.output}")
        else:
            print(content)

        if result.validation_result:
            print(f"\n--- Validation ---\n{result.validation_result.summary}")
    else:
        print(f"Pipeline failed: {result.errors}")
        sys.exit(1)
