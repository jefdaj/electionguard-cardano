from egc import await_blocks
import logging

LOG = logging.getLogger(__name__)

def wait_n_blocks(n: int = 1):
    n = int(n)
    LOG.warning(f'Waiting {n} blocks for any previous TXs to settle.')
    await_blocks(n)
