import os
import logging.config

def setup_logging(log_file=None):

    if log_file is None:
        log_file = 'node.log'

    # These are all probably worth looking at again if/when we have mysterious
    # issues. But the rest of the time they're pretty noisy.
    logging.getLogger('websockets').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.getLogger('ogmios').setLevel(logging.INFO)
    logging.getLogger('asyncio').setLevel(logging.INFO)
    logging.getLogger('aiohttp').setLevel(logging.INFO)
    logging.getLogger('pycardano').setLevel(logging.INFO)
    logging.getLogger('pycardano').handlers.clear()

    # Same with some of our code.
    logging.getLogger('egc.core.node').setLevel(logging.INFO)
    logging.getLogger('egc.core.ogmios').setLevel(logging.INFO)
    logging.getLogger('egc.core.plutus').setLevel(logging.INFO)
    logging.getLogger('egc.core.publisher').setLevel(logging.INFO)
    logging.getLogger('egc.core.subscriber').setLevel(logging.INFO)
    logging.getLogger('egc.nodes.admin').setLevel(logging.INFO)

    # Turn up the logging on sections we're actively debugging though.
    logging.getLogger('egc.core.records').setLevel(logging.DEBUG)
    logging.getLogger('egc.nodes.ipfs').setLevel(logging.DEBUG)

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
