import logging
from os import environ
from os.path import realpath
from pathlib import Path
from sys import modules

LOG = logging.getLogger(__name__)

PLUTUS_JSON_PATH_PROD   = realpath(Path(__file__).parent / '../../../onchain/election-plutus.json')
PLUTUS_JSON_PATH_TRACED = PLUTUS_JSON_PATH_PROD.replace('.json', '-traced.json')

# Explicit env var wins; otherwise default to traced under pytest, prod elsewhere.
# TODO name this something shorter/friendlier?
_env = environ.get("ELECTION_PLUTUS_VARIANT", "").lower()
if _env == "traced":
    USE_TRACED = True
elif _env == "prod":
    USE_TRACED = False
else:
    USE_TRACED = "pytest" in modules

PLUTUS_JSON_PATH = PLUTUS_JSON_PATH_TRACED if USE_TRACED else PLUTUS_JSON_PATH_PROD

LOG.info(
    f"Plutus blueprint JSON: {PLUTUS_JSON_PATH} (variant='{_env}', traced={USE_TRACED})"
)
