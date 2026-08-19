import pytest
from typing import List
from pprint import pformat
from egc import *
import time
import typing
from dataclasses import asdict
from collections import Counter

import logging
LOG = logging.getLogger(__name__)

from . import example_data
from . import json_utils
from . import py_utils

# TODO move some of this to env-specific helper/util libs

# Aliases for convenience and documentation.
# In our tests, the convention is that each package tests/integration/<package>
# is a particular usage path through the contract. Most fixtures are package
# scoped.
# TODO these might be more confusing than helpful, right?
# global_fixture       = pytest.fixture(scope='session')
# per_election_fixture = pytest.fixture(scope='module')
# per_network_fixture  = pytest.fixture(scope='package')


# TODO where should this live?
def isinstance_of_union(obj, union_type) -> bool:
    return isinstance(obj, typing.get_args(union_type))


# TODO move to channel.py
def is_channelstate(obj) -> bool:
    return isinstance_of_union(obj, ChannelState)


def sub_s0(sub_id: ChannelId, sub_vkh: VerificationKeyHash) -> ChannelState:
    return SubChannel(state=SubChannelState(
        channel_id  = sub_id,
        publisher   = sub_vkh.payload,
        ipfs_node   = NoIpfsNode(),
        new_records = [],
        seq         = 0,
    ))


def assert_tx(node_: ElectionNode, state: Optional[ChannelState], tx: Transaction):
    # This seems trivial, but would be a good place to
    # also assert nodes converge after every tx if needed,
    # or gather any other per-tx tests.
    assert isinstance(node_, ElectionNode)
    assert isinstance(tx, Transaction)
    if state is not None:
        assert isinstance_of_union(state, ChannelState)


def assert_nodes_have_same_history(nodes: list[ElectionNode]):
    """You probably want assert_nodes_converge below, unless you don't know
    what the phases/states should be beforehand."""
    if len(nodes) < 2:
        return
    ref_node = nodes[0]; other_nodes = nodes[1:]
    with ref_node.subscriber._history_lock:
        ref_hist = ref_node.subscriber._history
        for n in other_nodes:
            with n.subscriber._history_lock:
                try:
                    assert n.subscriber._history == ref_hist
                except AssertionError:
                    r_str = ref_node.channel_str()
                    n_str = n.channel_str()
                    diff = safe_deepdiff(ref_hist, n.subscriber._history)
                    LOG.error(
                        f'Nodes {r_str} and {n_str} '
                        f'disagree on history:\n{pformat(diff)}\n'
                    )
                    raise


def assert_collateral(nodes: list[ElectionNode]):
    for node in nodes:
        try:
            name = node.channel_str()
            utxo = node.publisher.await_collateral()
            LOG.info(f'{name} has the expected collateral utxo.')
        except TimeoutError:
            LOG.error(f'{name} is missing the expected collateral utxo.')


def assert_no_collateral(nodes: list[ElectionNode]):
    for node in nodes:
        utxo = node.publisher.find_collateral_utxo()
        assert utxo is None
        LOG.info(f'{name} has no collateral utxo, as expected.')


def assert_node_phases_converge(
        nodes: list[ElectionNode],
        expected_phase: EgcPhase,
        interval = 5,
        timeout = 300,
    ):
    start = time.monotonic()
    deadline = start + timeout
    while True:
        now = time.monotonic()
        if now > deadline:
            msg = f'All {len(nodes)} nodes did not converge to {expected_phase} within {timeout}s.'
            LOG.error(msg)
            raise TimeoutError(msg)
        sec = int(now - start)
        phases_by_str = {n.channel_str(): n.current_phase() for n in nodes}
        phase_counts = Counter(phases_by_str.values())
        LOG.debug(f'phase_counts after {sec}s: {dict(phase_counts)}')
        if phase_counts[expected_phase] == len(nodes):
            LOG.debug(f'All {len(nodes)} nodes converged to {expected_phase} after {sec}s.')
            return
        time.sleep(interval)


def channel_state_masked(ch_state):
    """Mask parts of the chanel state that aren't known in test fixtures to
    make testing by equality work."""
    LOG.debug(f'ch_state: {ch_state}')
    if ch_state is None:
        return None
    masked = deep_replace(ch_state, 'state.ipfs_node', 'masked')
    LOG.debug(f'masked: {masked}')
    return masked


def assert_node_states_converge(
        expected_states: list[ tuple[ElectionNode, Optional[ChannelState]] ],
        interval = 5,
        timeout = 300,
    ):
    """For each node, check that each actual channel state is as expected.
    A state of None here means that node's channel should be closed.
    """
    n = len(expected_states) # number of nodes and also states being checked per node
    start = time.monotonic()
    deadline = start + timeout
    while True:
        now = time.monotonic()
        sec = int(now - start)
        diffs = []
        for (node_to_test, _) in expected_states:
            for (node_for_id, expected_state) in expected_states:
                ch_id  = node_for_id.channel_id()
                ch_str = node_for_id.channel_str()
                actual_state  = node_to_test.current_state(ch_id)
                expected_mask = channel_state_masked(expected_state)
                actual_mask   = channel_state_masked(actual_state)
                try:
                    assert expected_mask == actual_mask
                except AssertionError as e:
                    diff = safe_deepdiff(expected_mask, actual_mask)
                    diffs.append(diff)
        if diffs:
            diff_counts = dict(Counter([pformat(d) for d in diffs]))
            msg = f'After {sec}s, there are still {len(diffs)} unexpected channel states:\n{pformat(diff_counts)}'
            if now > deadline:
                raise TimeoutError(msg) # TODO ValueError?
            else:
                LOG.warning(msg)
                time.sleep(interval)
        else:
            msg = f'After {sec}s, all {n} nodes converged to the expected channel states.'
            LOG.info(msg)
            return


def assert_nodes_converge(
        expected_states: list[ Tuple[ElectionNode, Optional[ChannelState]] ],
        expected_phase: EgcPhase = None,
        interval = 5,
        timeout = 300,
    ):
    """The inputs here are a state per node, but that's just a convenient format
    for passing the args. A state of None means the channel is closed."""
    nodes = [n for (n, _) in expected_states]
    assert_node_phases_converge(nodes, expected_phase, interval, timeout)
    assert_node_states_converge(expected_states, interval, timeout)
    assert_nodes_have_same_history(nodes)
    # TODO also assert (separately) that all records are fetched?
