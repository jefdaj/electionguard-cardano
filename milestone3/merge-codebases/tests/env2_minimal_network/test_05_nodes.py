import pytest
from egc import *
from ..lib import assert_nodes_converge
import logging

LOG = logging.getLogger(__name__)

def test_init_admin(admin: AdminNode):
    assert isinstance(admin, AdminNode)
    assert isinstance(admin.election, ElectionContext)
    assert isinstance(admin.publisher, ElectionPublisher)
    assert isinstance(admin.subscriber, ElectionSubscriber)
    assert admin.current_phase() == EgcPhase.CONFIG_ANNOUNCE

def test_init_subchannel_nodes(
        subchannel_nodes: list[ElectionNode],
    ):
    for n in subchannel_nodes:
        s = n.channel_str()
        assert issubclass(type(n), ElectionNode), f'{s} not a type of ElectionNode'
        assert isinstance(n.election, ElectionContext), f'{s}.election not an ElectionContext'
        assert isinstance(n.publisher, ElectionPublisher), f'{s}.publisher not an ElectionPublisher'
        assert isinstance(n.subscriber, ElectionSubscriber), f'{s}.subscriber not an ElectionSubscriber'
        assert n.current_phase() == EgcPhase.CONFIG_ANNOUNCE
    # TODO assert states?
    # TODO or, is this not a testnet test anymore?
