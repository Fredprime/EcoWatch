"""Lightweight, PII-free in-process HTTP metrics collector."""

import threading


class MetricsRegistry:
    """Thread-safe counters for request health and latency without PII or secrets."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._activeRequests = 0
        self._requestsByStatusClass: dict[str, int] = {
            "2xx": 0,
            "3xx": 0,
            "4xx": 0,
            "5xx": 0,
        }
        self._rateLimitedTotal = 0
        self._durationMsSum = 0.0
        self._durationMsCount = 0

    def inc_active(self) -> None:
        with self._lock:
            self._activeRequests += 1

    def dec_active(self) -> None:
        with self._lock:
            self._activeRequests = max(0, self._activeRequests - 1)

    def record_response(self, statusCode: int, durationMs: float) -> None:
        statusClass = f"{statusCode // 100}xx"
        with self._lock:
            if statusClass in self._requestsByStatusClass:
                self._requestsByStatusClass[statusClass] += 1
            if statusCode == 429:
                self._rateLimitedTotal += 1
            self._durationMsSum += max(0.0, durationMs)
            self._durationMsCount += 1

    def render_prometheus(self) -> str:
        with self._lock:
            lines = [
                "# HELP ecowatch_active_requests In-flight HTTP requests",
                "# TYPE ecowatch_active_requests gauge",
                f"ecowatch_active_requests {self._activeRequests}",
                "# HELP ecowatch_http_requests_total Completed HTTP requests by status class",
                "# TYPE ecowatch_http_requests_total counter",
            ]
            for statusClass, count in self._requestsByStatusClass.items():
                lines.append(
                    f'ecowatch_http_requests_total{{status_class="{statusClass}"}} {count}'
                )
            lines.extend(
                [
                    "# HELP ecowatch_http_rate_limited_total Total HTTP 429 responses",
                    "# TYPE ecowatch_http_rate_limited_total counter",
                    f"ecowatch_http_rate_limited_total {self._rateLimitedTotal}",
                    "# HELP ecowatch_http_request_duration_ms_sum Total request duration (ms)",
                    "# TYPE ecowatch_http_request_duration_ms_sum counter",
                    f"ecowatch_http_request_duration_ms_sum {self._durationMsSum:.2f}",
                    "# HELP ecowatch_http_request_duration_ms_count Total timed HTTP requests",
                    "# TYPE ecowatch_http_request_duration_ms_count counter",
                    f"ecowatch_http_request_duration_ms_count {self._durationMsCount}",
                ]
            )
        return "\n".join(lines) + "\n"


metricsRegistry = MetricsRegistry()
