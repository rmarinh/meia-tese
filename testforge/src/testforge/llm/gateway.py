"""Unified LLM gateway using LiteLLM."""

from __future__ import annotations

import logging

import litellm

from testforge.config import settings

logger = logging.getLogger("testforge.llm")

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True


async def complete(
    prompt: str,
    system: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: str | None = None,
) -> str:
    """Send a completion request to the configured LLM.

    Returns the text content of the response.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    model_name = model or settings.llm_model
    temp = temperature if temperature is not None else settings.llm_temperature
    max_tok = max_tokens or settings.llm_max_tokens

    kwargs: dict = {
        "model": model_name,
        "messages": messages,
        "temperature": temp,
        "max_tokens": max_tok,
    }

    if settings.llm_api_key:
        kwargs["api_key"] = settings.llm_api_key
    if settings.llm_base_url:
        kwargs["api_base"] = settings.llm_base_url

    logger.info("LLM request: model=%s, temperature=%.2f, max_tokens=%d", model_name, temp, max_tok)

    response = await litellm.acompletion(**kwargs)
    content = response.choices[0].message.content

    logger.info(
        "LLM response: %d chars, usage=%s",
        len(content) if content else 0,
        getattr(response, "usage", "N/A"),
    )

    return content or ""
