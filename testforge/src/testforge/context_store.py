"""Application context store — persistent memory per target app."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from testforge.config import settings
from testforge.models.app_context import AppContext, RunRecord
from testforge.models.results import ValidationResult
from testforge.models.test_model import EndpointMap, TestSuite

logger = logging.getLogger("testforge.context_store")


class ContextStore:
    """Persistent storage for application contexts.

    Each target application gets its own context file that accumulates
    knowledge across pipeline runs — endpoints, patterns, coverage, history.
    """

    def __init__(self, store_dir: Path | None = None):
        self.store_dir = store_dir or (settings.workspace_dir / "contexts")
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _context_path(self, app_id: str) -> Path:
        return self.store_dir / f"{app_id}.json"

    def list_apps(self) -> list[str]:
        """List all known application IDs."""
        return [p.stem for p in self.store_dir.glob("*.json")]

    def get(self, app_id: str) -> AppContext | None:
        """Load an application context."""
        path = self._context_path(app_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return AppContext(**data)

    def create(self, app_name: str, base_url: str, description: str = "") -> AppContext:
        """Create a new application context."""
        app_id = f"{app_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}"
        ctx = AppContext(
            app_id=app_id,
            app_name=app_name,
            base_url=base_url,
            description=description,
        )
        self._save(ctx)
        logger.info("Created context for app: %s (%s)", app_name, app_id)
        return ctx

    def get_or_create(self, app_name: str, base_url: str, description: str = "") -> AppContext:
        """Get existing context by app_name or create a new one."""
        for app_id in self.list_apps():
            ctx = self.get(app_id)
            if ctx and ctx.app_name == app_name and ctx.base_url == base_url:
                return ctx
        return self.create(app_name, base_url, description)

    def update_from_run(
        self,
        ctx: AppContext,
        mode: str,
        test_suite: TestSuite | None,
        validation: ValidationResult | None,
        endpoint_map: EndpointMap | None = None,
    ) -> AppContext:
        """Update context after a pipeline run."""
        ctx.updated_at = datetime.now()

        # Merge endpoint map
        if endpoint_map:
            if ctx.endpoint_map is None:
                ctx.endpoint_map = endpoint_map
            else:
                existing = {(ep.method, ep.path) for ep in ctx.endpoint_map.endpoints}
                for ep in endpoint_map.endpoints:
                    if (ep.method, ep.path) not in existing:
                        ctx.endpoint_map.endpoints.append(ep)

        # Track generated test names (to avoid duplicates)
        if test_suite:
            for test in test_suite.tests:
                if test.name not in ctx.known_test_names:
                    ctx.known_test_names.append(test.name)

        # Track tested endpoints
        if test_suite:
            for test in test_suite.tests:
                if test.target_method and test.target_endpoint:
                    key = f"{test.target_method} {test.target_endpoint}"
                    if key not in ctx.tested_endpoints:
                        ctx.tested_endpoints.append(key)

        # Update coverage gaps
        if ctx.endpoint_map:
            all_endpoints = {
                f"{ep.method} {ep.path}" for ep in ctx.endpoint_map.endpoints
            }
            tested = set(ctx.tested_endpoints)
            ctx.untested_endpoints = sorted(all_endpoints - tested)

        # Record run
        run_record = RunRecord(
            run_id=uuid.uuid4().hex[:8],
            mode=mode,
            tests_generated=test_suite.test_count if test_suite else 0,
            tests_passed=validation.execution_result.passed if validation and validation.execution_result else 0,
            tests_failed=validation.execution_result.failed if validation and validation.execution_result else 0,
        )

        ctx.run_history.append(run_record)
        ctx.total_tests_generated += run_record.tests_generated
        ctx.total_tests_passed += run_record.tests_passed
        ctx.total_tests_failed += run_record.tests_failed

        self._save(ctx)
        logger.info(
            "Updated context %s: %d runs, %d total tests, %d endpoints covered",
            ctx.app_id,
            len(ctx.run_history),
            ctx.total_tests_generated,
            len(ctx.tested_endpoints),
        )
        return ctx

    def _save(self, ctx: AppContext) -> None:
        path = self._context_path(ctx.app_id)
        path.write_text(
            ctx.model_dump_json(indent=2),
            encoding="utf-8",
        )
