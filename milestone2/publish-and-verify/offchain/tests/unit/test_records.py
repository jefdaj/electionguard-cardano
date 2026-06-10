import json
import pytest
from egc import *
import logging
from pathlib import Path
from typing import Tuple
from pprint import pprint

LOG = logging.getLogger(__name__)

# TODO round-trip all static records to test bytes encode/decode

# def test_roundtrip_static_records():
