import os
import logging
from enum import Enum
from pathlib import Path

from ..env import EGC_PLUTUS_MODE

LOG = logging.getLogger(__name__)


# Some glue code to load the correct plutus variant based on env vars.


# TODO set in all the important entrypoints
EGC_PLUTUS_DIR = os.environ.get(
    "EGC_PLUTUS_DIR",
    str(Path(__file__).parents[3].absolute() / 'aiken'),
)

PLUTUS_JSON_PATH = Path(EGC_PLUTUS_DIR) / f'egc-plutus-{EGC_PLUTUS_MODE}.json'

LOG.info(f'Plutus blueprint: {PLUTUS_JSON_PATH}')
