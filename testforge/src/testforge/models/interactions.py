"""Models for captured interactions (HTTP exchanges, browser events, etc.)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class HTTPExchange(BaseModel):
    """A single captured HTTP request/response pair."""

    method: str
    url: str
    path: str
    query_params: dict[str, str] = {}
    request_headers: dict[str, str] = {}
    request_body: Any | None = None
    request_content_type: str | None = None

    status_code: int
    response_headers: dict[str, str] = {}
    response_body: Any | None = None
    response_content_type: str | None = None

    duration_ms: float | None = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @property
    def is_json_request(self) -> bool:
        return bool(self.request_content_type and "json" in self.request_content_type)

    @property
    def is_json_response(self) -> bool:
        return bool(self.response_content_type and "json" in self.response_content_type)

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 400


class BrowserEvent(BaseModel):
    """A captured browser interaction event."""

    action: Literal["click", "fill", "navigate", "select", "check", "wait", "assert"]
    selector: str | None = None
    value: str | None = None
    url: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class InteractionRecord(BaseModel):
    """A complete interaction recording session."""

    session_id: str
    app_name: str
    base_url: str
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: datetime | None = None

    http_exchanges: list[HTTPExchange] = []
    browser_events: list[BrowserEvent] = []
    metadata: dict[str, Any] = {}

    @property
    def unique_endpoints(self) -> set[tuple[str, str]]:
        return {(ex.method, ex.path) for ex in self.http_exchanges}
