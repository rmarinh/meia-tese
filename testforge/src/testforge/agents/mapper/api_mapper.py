"""Mapper Agent — converts HTTP traffic into endpoint maps."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel

from testforge.agents.base import BaseAgent
from testforge.models.interactions import HTTPExchange, InteractionRecord
from testforge.models.test_model import EndpointInfo, EndpointMap


class MapperInput(BaseModel):
    """Input for the Mapper Agent."""

    interaction_record: InteractionRecord


class MapperOutput(BaseModel):
    """Output of the Mapper Agent."""

    endpoint_map: EndpointMap


class MapperAgent(BaseAgent[MapperInput, MapperOutput]):
    """Builds endpoint maps from observed HTTP traffic."""

    def __init__(self):
        super().__init__("MapperAgent")

    async def run(self, input_data: MapperInput) -> MapperOutput:
        record = input_data.interaction_record
        exchanges = record.http_exchanges

        # Group exchanges by (method, normalized_path)
        grouped: dict[tuple[str, str], list[HTTPExchange]] = defaultdict(list)
        for ex in exchanges:
            normalized = self._normalize_path(ex.path)
            grouped[(ex.method, normalized)].append(ex)

        endpoints = []
        for (method, path), exs in sorted(grouped.items()):
            endpoint = self._build_endpoint_info(method, path, exs)
            endpoints.append(endpoint)

        # Detect dependencies
        dependencies = self._detect_dependencies(endpoints, exchanges)

        # Detect auth patterns
        auth_patterns = self._detect_auth_patterns(exchanges)

        # Common headers
        common_headers = self._detect_common_headers(exchanges)

        endpoint_map = EndpointMap(
            app_name=record.app_name,
            base_url=record.base_url,
            endpoints=endpoints,
            auth_patterns=auth_patterns,
            common_headers=common_headers,
            dependencies=dependencies,
        )

        self.logger.info(
            "Mapped %d endpoints from %d exchanges",
            len(endpoints),
            len(exchanges),
        )

        return MapperOutput(endpoint_map=endpoint_map)

    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing numeric IDs with placeholders."""
        # /users/123 → /users/{id}
        parts = path.strip("/").split("/")
        normalized = []
        for part in parts:
            if re.match(r"^\d+$", part):
                normalized.append("{id}")
            elif re.match(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                part,
                re.IGNORECASE,
            ):
                normalized.append("{uuid}")
            else:
                normalized.append(part)
        return "/" + "/".join(normalized)

    def _build_endpoint_info(
        self, method: str, path: str, exchanges: list[HTTPExchange]
    ) -> EndpointInfo:
        """Build endpoint info from a group of exchanges to the same endpoint."""
        status_codes = sorted(set(ex.status_code for ex in exchanges))

        # Detect auth
        auth_required = any(
            "authorization" in (k.lower() for k in ex.request_headers.keys())
            for ex in exchanges
        )
        auth_type = None
        if auth_required:
            for ex in exchanges:
                auth_header = next(
                    (v for k, v in ex.request_headers.items() if k.lower() == "authorization"),
                    None,
                )
                if auth_header:
                    if auth_header.startswith("Bearer "):
                        auth_type = "bearer"
                    elif auth_header.startswith("Basic "):
                        auth_type = "basic"
                    else:
                        auth_type = "custom"
                    break

        # Collect query params
        all_params = set()
        for ex in exchanges:
            all_params.update(ex.query_params.keys())

        # Detect path params
        path_params = re.findall(r"\{(\w+)\}", path)

        # Infer request schema from JSON bodies
        request_schema = None
        for ex in exchanges:
            if ex.is_json_request and isinstance(ex.request_body, dict):
                request_schema = self._infer_schema(ex.request_body)
                break

        # Infer response schema
        response_schema = None
        sample_response = None
        for ex in exchanges:
            if ex.is_json_response and ex.is_success:
                sample_response = ex.response_body
                if isinstance(ex.response_body, dict):
                    response_schema = self._infer_schema(ex.response_body)
                break

        # Sample request
        sample_request = None
        for ex in exchanges:
            if ex.request_body:
                sample_request = ex.request_body
                break

        return EndpointInfo(
            method=method,
            path=path,
            request_schema=request_schema,
            response_schema=response_schema,
            auth_required=auth_required,
            auth_type=auth_type,
            query_params=sorted(all_params),
            path_params=path_params,
            observed_status_codes=status_codes,
            sample_request=sample_request,
            sample_response=sample_response,
        )

    def _infer_schema(self, data: dict) -> dict[str, Any]:
        """Infer a simple JSON schema from a sample object."""
        schema: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str):
                schema[key] = "string"
            elif isinstance(value, bool):
                schema[key] = "boolean"
            elif isinstance(value, int):
                schema[key] = "integer"
            elif isinstance(value, float):
                schema[key] = "number"
            elif isinstance(value, list):
                schema[key] = "array"
            elif isinstance(value, dict):
                schema[key] = self._infer_schema(value)
            elif value is None:
                schema[key] = "nullable"
        return schema

    def _detect_dependencies(
        self,
        endpoints: list[EndpointInfo],
        exchanges: list[HTTPExchange],
    ) -> dict[str, list[str]]:
        """Detect endpoint dependencies based on data flow patterns.

        e.g., POST /users returns an ID that's used in GET /users/{id}
        """
        deps: dict[str, list[str]] = {}

        # Simple heuristic: endpoints with path params likely depend on
        # creation endpoints (POST without path params on same resource)
        resource_creators: dict[str, str] = {}
        for ep in endpoints:
            if ep.method == "POST" and not ep.path_params:
                resource = ep.path.strip("/").split("/")[0] if ep.path != "/" else ""
                if resource:
                    resource_creators[resource] = f"{ep.method} {ep.path}"

        for ep in endpoints:
            if ep.path_params:
                resource = ep.path.strip("/").split("/")[0] if ep.path != "/" else ""
                if resource in resource_creators:
                    key = f"{ep.method} {ep.path}"
                    deps[key] = [resource_creators[resource]]

        return deps

    def _detect_auth_patterns(self, exchanges: list[HTTPExchange]) -> list[str]:
        """Detect authentication patterns used across exchanges."""
        patterns = set()
        for ex in exchanges:
            for key, value in ex.request_headers.items():
                if key.lower() == "authorization":
                    if value.startswith("Bearer "):
                        patterns.add("Bearer token")
                    elif value.startswith("Basic "):
                        patterns.add("Basic auth")
                    else:
                        patterns.add("Custom auth header")
                elif key.lower() == "x-api-key":
                    patterns.add("API key header")
            # Check cookies
            if any(k.lower() == "cookie" for k in ex.request_headers.keys()):
                patterns.add("Cookie-based session")
        return sorted(patterns)

    def _detect_common_headers(self, exchanges: list[HTTPExchange]) -> dict[str, str]:
        """Find headers that appear in all requests."""
        if not exchanges:
            return {}

        # Headers present in all exchanges
        common: dict[str, str] = {}
        first_headers = {
            k.lower(): v for k, v in exchanges[0].request_headers.items()
        }

        skip_headers = {
            "host", "user-agent", "accept", "accept-encoding",
            "accept-language", "connection", "content-length",
            "content-type", "cookie", "authorization",
        }

        for header, value in first_headers.items():
            if header in skip_headers:
                continue
            if all(
                any(k.lower() == header for k in ex.request_headers)
                for ex in exchanges
            ):
                common[header] = value

        return common
