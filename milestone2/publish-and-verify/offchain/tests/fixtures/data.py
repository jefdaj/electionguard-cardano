import pytest
from pycardano import *
from egc import *
from data.static_records import *
from test_utils import global_fixture
import logging

LOG = logging.getLogger(__name__)

@global_fixture
def static_phases():
    return STATIC_PHASES
