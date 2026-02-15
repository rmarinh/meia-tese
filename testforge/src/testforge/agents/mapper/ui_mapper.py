"""UI interaction mapper (Phase 3)."""

from __future__ import annotations

import logging

logger = logging.getLogger("testforge.mapper.ui_mapper")


class UIMapper:
    """Placeholder for browser event → interaction graph mapping.

    Will be implemented in Phase 3 for UI test generation.
    """

    async def map_interactions(self, events: list[dict]) -> dict:
        raise NotImplementedError("UI mapping is planned for Phase 3")
