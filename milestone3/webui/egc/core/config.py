import os
import logging
from enum import Enum
from pathlib import Path

LOG = logging.getLogger(__name__)

class ElectionMode(Enum):
    PROD = 'prod'
    TEST = 'test'

    @classmethod
    def current(cls) -> 'Mode':
        raw = os.environ.get('EGC_MODE', 'prod').lower()
        try:
            return cls(raw)
        except ValueError:
            raise RuntimeError(
                f'EGC_MODE must be one of {[m.value for m in cls]}, got {raw!r}'
            )

MODE = ElectionMode.current()
IS_TEST = MODE is ElectionMode.TEST

PLUTUS_JSON_PATH_PROD = (
    Path(__file__).parents[2].absolute() /
    'onchain/election-plutus.json'
)
PLUTUS_JSON_PATH_TEST = Path(
    str(PLUTUS_JSON_PATH_PROD).replace('.json', '-traced.json')
)

PLUTUS_JSON_PATH = PLUTUS_JSON_PATH_TEST if IS_TEST else PLUTUS_JSON_PATH_PROD

if IS_TEST:
    LOG.warning('=' * 60)
    LOG.warning('RUNNING IN TEST MODE — secrets will be logged!')
    LOG.warning('Using traced Plutus script: %s', PLUTUS_JSON_PATH)
    LOG.warning('=' * 60)
