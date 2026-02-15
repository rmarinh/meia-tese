"""Observer Agent — captures HTTP traffic via mitmproxy."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from testforge.agents.base import BaseAgent
from testforge.models.interactions import HTTPExchange, InteractionRecord

logger = logging.getLogger("testforge.observer.http_proxy")


class ObserverInput(BaseModel):
    """Input for the Observer Agent."""

    app_name: str
    base_url: str
    proxy_port: int = 8080
    # For non-proxy mode: accept pre-captured exchanges
    captured_exchanges: list[dict[str, Any]] = []
    har_file_path: str | None = None


class ObserverOutput(BaseModel):
    """Output of the Observer Agent."""

    interaction_record: InteractionRecord


class ObserverAgent(BaseAgent[ObserverInput, ObserverOutput]):
    """Captures HTTP traffic from a running application.

    Supports multiple capture modes:
    - Live proxy via mitmproxy (requires mitmproxy optional dependency)
    - Import from HAR file
    - Direct exchange injection (for testing)
    """

    def __init__(self):
        super().__init__("ObserverAgent")

    async def run(self, input_data: ObserverInput) -> ObserverOutput:
        session_id = uuid.uuid4().hex[:12]

        record = InteractionRecord(
            session_id=session_id,
            app_name=input_data.app_name,
            base_url=input_data.base_url,
        )

        # Mode 1: Pre-captured exchanges (for testing/import)
        if input_data.captured_exchanges:
            for ex_data in input_data.captured_exchanges:
                record.http_exchanges.append(HTTPExchange(**ex_data))

        # Mode 2: HAR file import
        elif input_data.har_file_path:
            exchanges = self._parse_har_file(input_data.har_file_path)
            record.http_exchanges.extend(exchanges)

        record.ended_at = datetime.now()

        self.logger.info(
            "Captured %d HTTP exchanges for %s",
            len(record.http_exchanges),
            input_data.app_name,
        )

        return ObserverOutput(interaction_record=record)

    def _parse_har_file(self, har_path: str) -> list[HTTPExchange]:
        """Parse a HAR (HTTP Archive) file into HTTPExchange objects."""
        from pathlib import Path

        har_data = json.loads(Path(har_path).read_text(encoding="utf-8"))
        exchanges = []

        for entry in har_data.get("log", {}).get("entries", []):
            req = entry.get("request", {})
            resp = entry.get("response", {})

            url = req.get("url", "")
            # Extract path from URL
            from urllib.parse import urlparse

            parsed = urlparse(url)
            path = parsed.path

            # Parse query params
            query_params = {}
            for qp in req.get("queryString", []):
                query_params[qp["name"]] = qp["value"]

            # Parse headers
            req_headers = {h["name"]: h["value"] for h in req.get("headers", [])}
            resp_headers = {h["name"]: h["value"] for h in resp.get("headers", [])}

            # Parse bodies
            req_body = None
            req_content_type = None
            if req.get("postData"):
                req_body = req["postData"].get("text")
                req_content_type = req["postData"].get("mimeType")
                if req_content_type and "json" in req_content_type and req_body:
                    try:
                        req_body = json.loads(req_body)
                    except json.JSONDecodeError:
                        pass

            resp_body = None
            resp_content_type = None
            if resp.get("content"):
                resp_body = resp["content"].get("text")
                resp_content_type = resp["content"].get("mimeType")
                if resp_content_type and "json" in resp_content_type and resp_body:
                    try:
                        resp_body = json.loads(resp_body)
                    except json.JSONDecodeError:
                        pass

            duration = entry.get("time", 0)

            exchanges.append(
                HTTPExchange(
                    method=req.get("method", "GET"),
                    url=url,
                    path=path,
                    query_params=query_params,
                    request_headers=req_headers,
                    request_body=req_body,
                    request_content_type=req_content_type,
                    status_code=resp.get("status", 0),
                    response_headers=resp_headers,
                    response_body=resp_body,
                    response_content_type=resp_content_type,
                    duration_ms=duration,
                )
            )

        return exchanges


class MitmproxyAddon:
    """mitmproxy addon for live HTTP capture.

    Usage with mitmproxy:
        mitmdump -s path/to/http_proxy.py --set app_name=myapp

    Or programmatically:
        from mitmproxy.tools import main
    """

    def __init__(self):
        self.exchanges: list[HTTPExchange] = []
        self.logger = logging.getLogger("testforge.observer.mitmproxy_addon")

    def response(self, flow) -> None:
        """Called by mitmproxy when a response is received."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(flow.request.pretty_url)

            req_body = None
            req_content_type = flow.request.headers.get("content-type")
            if flow.request.content:
                try:
                    req_body = json.loads(flow.request.content)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    req_body = flow.request.content.decode("utf-8", errors="replace")

            resp_body = None
            resp_content_type = flow.response.headers.get("content-type")
            if flow.response.content:
                try:
                    resp_body = json.loads(flow.response.content)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    resp_body = flow.response.content.decode("utf-8", errors="replace")

            exchange = HTTPExchange(
                method=flow.request.method,
                url=flow.request.pretty_url,
                path=parsed.path,
                query_params=dict(flow.request.query or {}),
                request_headers=dict(flow.request.headers),
                request_body=req_body,
                request_content_type=req_content_type,
                status_code=flow.response.status_code,
                response_headers=dict(flow.response.headers),
                response_body=resp_body,
                response_content_type=resp_content_type,
                duration_ms=(
                    flow.response.timestamp_end - flow.request.timestamp_start
                )
                * 1000
                if flow.response.timestamp_end
                else None,
            )
            self.exchanges.append(exchange)
            self.logger.debug(
                "Captured: %s %s → %d",
                exchange.method,
                exchange.path,
                exchange.status_code,
            )
        except Exception:
            self.logger.exception("Failed to capture exchange")
