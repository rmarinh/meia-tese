"""LLM API call interceptor (Phase 4)."""

from __future__ import annotations

import logging

logger = logging.getLogger("testforge.observer.llm_calls")


class LLMCallInterceptor:
    """Placeholder for LLM API call interception.

    Will be implemented in Phase 4 for LLM application testing.
    """

    async def start_intercepting(self) -> None:
        raise NotImplementedError("LLM call interception is planned for Phase 4")
