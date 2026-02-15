"""Browser interaction recorder using Playwright (Phase 3)."""

from __future__ import annotations

import logging

logger = logging.getLogger("testforge.observer.browser")


class BrowserRecorder:
    """Placeholder for Playwright-based browser recording.

    Will be implemented in Phase 3 for UI test generation.
    """

    async def start_recording(self, url: str) -> None:
        raise NotImplementedError("Browser recording is planned for Phase 3")

    async def stop_recording(self) -> list[dict]:
        raise NotImplementedError("Browser recording is planned for Phase 3")
