import os
import logging.config

def setup_logging(log_file=None):

    if log_file is None:
        log_file = 'node.log'

    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.getLogger('ogmios').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

    logging.getLogger('egc.core.ogmios').setLevel(logging.DEBUG)
    logging.getLogger('egc.core.subscriber').setLevel(logging.DEBUG)
    # logging.getLogger('egc.core.node').setLevel(logging.DEBUG)
    # logging.getLogger('egc.core.phase').setLevel(logging.DEBUG)
    # logging.getLogger('egc.core.publisher').setLevel(logging.DEBUG)
    # logging.getLogger('egc.core.records').setLevel(logging.DEBUG)
    # logging.getLogger('egc.nodes.admin').setLevel(logging.DEBUG)
    # logging.getLogger('egc.nodes.ipfs').setLevel(logging.DEBUG)


    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": log_file,
                "maxBytes": 100_000_000,
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
