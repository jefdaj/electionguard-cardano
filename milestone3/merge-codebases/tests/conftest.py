import pytest
import logging

# Tell pytest to print diffs on assertions
pytest.register_assert_rewrite("helpers") # TODO tests.helpers?

def pytest_configure(config):
    # These are all probably worth looking at again if/when we have mysterious
    # API issues. But the rest of the time they're pretty noisy.
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.getLogger('ogmios').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('aiphttp').setLevel(logging.WARNING)

    # TODO dial down the subscriber too, either here or at the source

from .fixtures.data import *
