from os.path import realpath
from pathlib import Path
from sys import modules

PLUTUS_JSON_PATH_PROD   = realpath(Path(__file__).parent / '../../../onchain/election-plutus.json')
PLUTUS_JSON_PATH_TRACED = PLUTUS_JSON_PATH_PROD.replace('.json', '-traced.json')

IS_TEST_ENV = "pytest" in modules
if IS_TEST_ENV:
    PLUTUS_JSON_PATH = PLUTUS_JSON_PATH_TRACED
else:
    PLUTUS_JSON_PATH = PLUTUS_JSON_PATH_PROD
