import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any
from app.core.config import config


LOG_LEVEL = config.LOG_LEVEL.upper()


class JsonFormatter(logging.Formatter):
    _LOGRECORD_INTERNAL_ATTRS = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        log: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        invalid_keys: list[str] = []
        for key, value in record.__dict__.items():
            if key in self._LOGRECORD_INTERNAL_ATTRS or key.startswith("_"):
                continue

            if key.lower() != key:
                invalid_keys.append(key)
                continue

            log[key] = value

        if invalid_keys:
            log["_invalid_extra_keys"] = invalid_keys

        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)

        return json.dumps(log, ensure_ascii=False, default=str)


def get_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(JsonFormatter())
    logger.addHandler(stream_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger.propagate = False
    return logger


logger = get_logger()
