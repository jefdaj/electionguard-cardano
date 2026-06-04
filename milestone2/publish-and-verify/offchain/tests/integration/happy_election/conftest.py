import pytest
from egc import *

@pytest.fixture(scope='package')
def happy_admin_tx0(init_tx: Transaction) -> Transaction:
    # admin_tx0 is just the init_tx.
    # We re-export it here to avoid any confusion.
    return init_tx

@pytest.fixture(scope='package')
def happy_admin_tx1(
        admin: Admin,
        happy_admin_tx0: Transaction,
    ) -> Transaction:
    raise NotImplementedError
