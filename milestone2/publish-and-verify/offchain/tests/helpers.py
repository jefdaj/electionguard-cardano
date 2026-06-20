import pytest
from typing import List
from pprint import pformat
from egc import *
import logging
import time

LOG = logging.getLogger(__name__)

# Aliases for convenience and documentation.
# In our tests, the convention is that each package tests/integration/<package>
# is a particular usage path through the contract. Most fixtures are package
# scoped.
global_fixture       = pytest.fixture(scope='session')
per_election_fixture = pytest.fixture(scope='module')

def assert_nodes_in_sync(nodes: List[ElectionNode]):
    if len(nodes) < 2:
        LOG.warning('assert_nodes_in_sync called with < 2 nodes')
        return
    ch_strs = [n.channel_str() for n in nodes]
    # one node to compare the others against
    ref = nodes[0]; nodes = nodes[1:]
    ref.subscriber.sleep(10) # TODO remove
    for node in nodes:

        np = node.current_phase()
        rp = ref.current_phase()
        assert np == rp

        # TODO use interface here rather than raw history dict
        nh = node.subscriber._history
        rh = ref.subscriber._history
        assert nh == rh

    LOG.info(f'All {len(nodes)+1} nodes in sync: ' + ', '.join(s for s in ch_strs))
    # LOG.debug(f'Current state:\n\n{pformat(ref.subscriber.states)}\n')

# TODO rename _sub tests -> checkpoints and add cross-channel dependencies
def assert_node_state(
        node: ElectionNode,
        expected_state: ChannelState,
    ):
    assert isinstance(node, ElectionNode)
    assert isinstance(expected_state, ChannelState)
    node.subscriber.sleep(10) # TODO remove
    node_str = node.channel_str()
    # (state_utxo, actual_state) = node.state()
    state_utxo   = node.current_utxo()
    actual_state = node.current_state()
    LOG.debug(f'{node_str} latest state utxo: {state_utxo}')
    assert actual_state == expected_state
    LOG.debug(f'{node_str} state as expected: {actual_state}')

def sub_s0(sub_id: ChannelId, sub_vkh: VerificationKeyHash) -> ChannelState:
    return SubChannel(state=SubChannelState(
        channel_id  = sub_id,
        publisher   = sub_vkh.payload,
        new_records = [],
        seq         = 0,
    ))
