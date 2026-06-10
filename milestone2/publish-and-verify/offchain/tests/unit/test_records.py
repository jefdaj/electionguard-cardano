import json
import pytest
from egc import *
import logging
from pathlib import Path
from typing import Tuple
from pprint import pprint

LOG = logging.getLogger(__name__)

# TODO round-trip a few hand written records here to test byte encode/decode
