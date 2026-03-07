import json
import logging
import os
from datetime import datetime
from opentelemetry.trace import get_current_span


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        span = get_current_span()
        span_context = span.get_span_context() if span else None

        log = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": os.getenv("SERVICE_NAME", "auth-service"),
            "environment": os.getenv("ENVIRONMENT", "dev"),
            "trace_id": (
                format(span_context.trace_id, "032x")
                if span_context and span_context.trace_id != 0
                else None
            ),
            "span_id": (
                format(span_context.span_id, "016x")
                if span_context and span_context.span_id != 0
                else None
            ),
        }

        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)

        return json.dumps(log, ensure_ascii=False)



def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    root = logging.getLogger()
    root.setLevel(log_level)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
