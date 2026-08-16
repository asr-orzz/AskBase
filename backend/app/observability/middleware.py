from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY
from app.observability.tracing import get_tracer


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Records Prometheus metrics and OpenTelemetry spans for every HTTP request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in ("/metrics", "/health", "/openapi.json", "/docs", "/redoc"):
            return await call_next(request)

        method = request.method
        path_template = _get_route_pattern(request) or request.url.path

        tracer = get_tracer()
        with tracer.start_as_current_span(f"HTTP {method} {path_template}") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.route", path_template)

            start = time.perf_counter()
            try:
                response = await call_next(request)
                status = str(response.status_code)
                span.set_attribute("http.status_code", response.status_code)
            except Exception as e:
                status = "500"
                span.record_exception(e)
                raise
            finally:
                duration = time.perf_counter() - start
                REQUEST_COUNT.labels(method=method, endpoint=path_template, status_code=status).inc()
                REQUEST_LATENCY.labels(method=method, endpoint=path_template).observe(duration)

        return response


def _get_route_pattern(request: Request) -> str | None:
    """Extract the route pattern (e.g. /api/v1/knowledge-bases/{kb_id}) from the request."""
    route = request.scope.get("route")
    if route and hasattr(route, "path"):
        return route.path
    return None
