import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_admin_keys(admin_keys: KeyPair):
    assert isinstance(admin_keys, KeyPair)
    assert isinstance(admin_keys.sk, SigningKey)
    assert isinstance(admin_keys.addr, Address)
    assert isinstance(admin_keys.vkh, VerificationKeyHash)

def test_init_admin_node(admin_node: AdminNode):
    assert isinstance(admin_node, AdminNode)
    assert isinstance(admin_node.election, ElectionContext)
    assert isinstance(admin_node.publisher, ElectionPublisher)
    assert isinstance(admin_node.subscriber, ElectionSubscriber)
