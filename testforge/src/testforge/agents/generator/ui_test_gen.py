"""Playwright UI test generator (Phase 3)."""

from __future__ import annotations

import logging

logger = logging.getLogger("testforge.generator.ui_test_gen")


class UITestGenerator:
    """Placeholder for Playwright test generation.

    Will be implemented in Phase 3 for browser-based UI test generation.
    """

    async def generate(self, user_flows: list[dict]) -> str:
        raise NotImplementedError("UI test generation is planned for Phase 3")
