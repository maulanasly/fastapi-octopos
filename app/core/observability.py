"""Request-ID middleware and structured logging.

Every request gets a UUID (honouring an incoming ``X-Request-ID`` so
clients can correlate) exposed as a contextvar for log formatters and
echoed back on the response. Logging is configured once via
``setup_logging`` with a request-id-aware formatter.
"""

import contextvars
import json
import logging
import logging.config
import os
import uuid

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


class RequestIDMiddleware:
    """Attach a request id to every request/response and log record."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        incoming = headers.get(b"x-request-id")
        if incoming:
            try:
                request_id = incoming.decode("ascii").strip()
            except UnicodeDecodeError:
                request_id = ""
            if not request_id:
                request_id = str(uuid.uuid4())
        else:
            request_id = str(uuid.uuid4())

        token = _request_id.set(request_id)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            _request_id.reset(token)


def get_request_id() -> str:
    """Current request id, or '-' outside of a request."""
    return _request_id.get()


class _RequestIDFilter(logging.Filter):
    """Injects the active request id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class _JSONFormatter(logging.Formatter):
    """Machine-readable one-line JSON per record."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging() -> None:
    """Configure request-id-aware logging (JSON in production)."""
    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    json_logs = os.getenv("LOG_JSON", "").lower() in ("1", "true", "yes")
    fmt = "%(asctime)s %(levelname)s %(name)s [request_id=%(request_id)s] %(message)s"

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"request_id": {"()": _RequestIDFilter}},
            "formatters": {
                "console": {"format": fmt},
                "json": {"()": _JSONFormatter},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json" if json_logs else "console",
                    "filters": ["request_id"],
                }
            },
            "root": {"handlers": ["console"], "level": level},
        }
    )
