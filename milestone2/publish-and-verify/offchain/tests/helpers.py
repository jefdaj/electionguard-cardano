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

def assert_nodes_sync_in_5min(nodes: List[ElectionNode]):
    n = len(nodes)
    if n < 2:
        LOG.warning('assert_nodes_sync_in_5min called with < 2 nodes')
        return
    ch_strs = [node.channel_str() for node in nodes]
    # one node to compare the others against
    ref = nodes[0]; nodes = nodes[1:]
    # Wait to make sure they're not all in sync at the prev state.
    # TODO speed this back up after figuring out the sync bug
    time.sleep(60)
    w = 60 # "waited"
    while True:
        try:
            for node in nodes:

                np = node.current_phase()
                rp = ref.current_phase()
                assert np == rp

                # TODO use interface here rather than raw history dict
                nh = node.subscriber._history
                rh = ref.subscriber._history
                assert nh == rh

            LOG.info(
                f'All {n} nodes are in sync after {w} seconds: ' + ', '.join(s for s in ch_strs)
            )
            return
        except AssertionError:
            LOG.debug(f'All {len(nodes)+1} nodes not in sync after {w} seconds.')
            if w > 300:
                raise
            time.sleep(10)
            w += 10


# TODO rename _sub tests -> checkpoints and add cross-channel dependencies
def assert_node_state(
        node: ElectionNode,
        expected_state: ChannelState,
    ):
    assert isinstance(node, ElectionNode)
    assert isinstance(expected_state, ChannelState)
    node_str = node.channel_str()
    actual_state = node.current_state()
    LOG.debug(f'{node_str} actual state:   {pformat(actual_state)  }')
    LOG.debug(f'{node_str} expected state: {pformat(expected_state)}')
    assert actual_state == expected_state

def sub_s0(sub_id: ChannelId, sub_vkh: VerificationKeyHash) -> ChannelState:
    return SubChannel(state=SubChannelState(
        channel_id  = sub_id,
        publisher   = sub_vkh.payload,
        new_records = [],
        seq         = 0,
    ))
