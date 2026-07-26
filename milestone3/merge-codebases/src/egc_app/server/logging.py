import os
import logging.config

def setup_logging(log_file=None):
    if log_file is None:
        log_file = 'node.log'
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": log_file,
                "maxBytes": 10_000_000,
                "backupCount": 5,
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["file"]},
        "loggers": {
            "uvicorn":        {"handlers": ["file"], "level": "INFO", "propagate": False},
            "uvicorn.error":  {"handlers": ["file"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["file"], "level": "INFO", "propagate": False},
        },
    })
