import pytest
from typing import List
from pprint import pformat
from egc import *
import time
import typing
from dataclasses import asdict

import logging
LOG = logging.getLogger(__name__)

from . import example_data
from . import json_utils
from . import proc_utils

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
    # You probably want assert_nodes_converge below,
    # unless you don't know what the stages should be
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
            utxo = node.publisher.wait_for_collateral()
            LOG.info(f'{name} has the expected collateral utxo.')
        except TimeoutError:
            LOG.error(f'{name} is missing the expected collateral utxo.')


def assert_no_collateral(nodes: list[ElectionNode]):
    for node in nodes:
        utxo = node.publisher.find_collateral_utxo()
        assert utxo is None
        LOG.info(f'{name} has no collateral utxo, as expected.')


def assert_nodes_converge(
        expected_states: list[ Tuple[ElectionNode, Optional[ChannelState]] ],
        expected_phase: EgcPhase = None,
        interval = 1,
        timeout = 60,
    ):
    """The inputs here are a state per node, but that's just a convenient format
    for passing the args. What it actually does is:

    1. logs how many nodes have reached the expected channel states every 5 sec
    2. once all of them reach those states, assert that their phases and histories are also as expected

    The two are combined because we always want both, and to avoid a fixed
    delay before the equal history check. A state of None means the channel is closed."""

    n = len(expected_states) # both the number of nodes and number of states being checked

    for (node, state) in expected_states:
        assert isinstance(node, ElectionNode)
        if state is not None:
            assert is_channelstate(state)

    waited = 0
    while True:
        n_nodes_correct_prev = 0
        n_nodes_correct = 0

        for (node_to_test, _) in expected_states:
            node_str = node_to_test.channel_str()
            n_states_correct = 0

            # How many states does this node have correct so far?
            for (node_for_id, expected_state) in expected_states:
                state_str = node_for_id.channel_str()
                actual_state = node_to_test.current_state(node_for_id.channel_id())
                try:
                    assert expected_state == actual_state
                    n_states_correct += 1
                except AssertionError as e:
                    if waited >= timeout:
                        diff = safe_deepdiff(expected_state, actual_state)
                        LOG.debug(
                            f'{node_str} node has wrong {state_str} state'
                            f' after {waited}s:\n{pformat(diff)}'
                        )
                        LOG.error(
                            'Nodes did not converge on expected states'
                            f' within {timeout}s.'
                        )
                        raise
                    else:
                        continue # next node

            # How many nodes have them all correct?
            if n_states_correct == n:
                n_nodes_correct += 1

        # just to clean up the logs
        if n_nodes_correct != n_nodes_correct_prev:
            LOG.debug(
                f'After {waited} seconds, {n_nodes_correct}/{n}'
                ' nodes converged on expected states.'
            )
            n_nodes_correct_prev = n_nodes_correct

        if n_nodes_correct == n:
            for (n, _) in expected_states:
                p = n.current_phase()
                assert p == expected_phase, f"Node {n} should have phase {expected_phase}, but has {p}."
            LOG.debug(f"All nodes have the expected phase {expected_phase}.")
            try:
                # This normally works the first time, but occasionally fails.
                # Perhaps there's a same-but-spent update during?
                assert_nodes_have_same_history([n for (n, _) in expected_states])
                break
            except AssertionError as e:
                if waited >= timeout:
                    LOG.error(f'Nodes did not all have the same history within {timeout}s.')
                else:
                    LOG.debug('Nodes do not all have the same history yet.')

        time.sleep(interval)
        waited += interval
