import pytest
from pycardano import *
from egc import *
import logging

LOG = logging.getLogger(__name__)

@pytest.fixture(scope='package')
def happy_admin_tx0(
        funder: Funder,
        script: ElectionScript,
        admin_vkh: VerificationKeyHash
    ) -> Transaction:
    """Yields an already submitted and confirmed InitElection transaction.
    This one is special because it also cleans up by running BurnTestTokens if
    needed. All other Transaction fixtures should depend on this one.
    """
    # TODO how to handle the electionguard vs cardano keys? do we need anything special?
    (admin_tx0, _) = funder.init_election(script=script, admin_vkh=admin_vkh, admin_ada=10) # TODO what's a good amount?
    funder.publisher.wait_for_confirmation(admin_tx0)

    # All other tests happen here
    yield admin_tx0

    # TODO only burn if the election hasn't ended on its own yet
    burn_tx = funder.burn_test_tokens()
    funder.publisher.wait_for_confirmation(burn_tx)
