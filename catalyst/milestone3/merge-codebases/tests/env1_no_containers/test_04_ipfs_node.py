import pytest
from egc import *
from pycardano.serialization import ByteString

# TODO test addr_hints

def test_ipfs_node_roundtrip_cbor():
    pid  = '12D3KooWPAwuXAV3XgW4ik4G6CYPV1VmtFX7Kk9BAEEsPSmPHFX3'
    node = IpfsNode(peer_id=pid, addr_hints=[])
    assert IpfsNode.from_cbor(node.to_cbor_hex()) == node

def test_ipfs_peerid_roundtrip_string():
    pid  = '12D3KooWPAwuXAV3XgW4ik4G6CYPV1VmtFX7Kk9BAEEsPSmPHFX3'
    node = IpfsNode(peer_id=pid, addr_hints=[])
    assert ipfs_peerid_to_string(node.peer_id) == pid

def test_some_ipfs_node_roundtrip_cbor():
    pid  = '12D3KooWPAwuXAV3XgW4ik4G6CYPV1VmtFX7Kk9BAEEsPSmPHFX3'
    node = IpfsNode(peer_id=pid, addr_hints=[])
    opt  = SomeIpfsNode(value=node)
    assert decode_option_ipfs_node(opt.to_cbor_hex()) == opt

def test_no_ipfs_node_roundtrip_cbor():
    opt = NoIpfsNode()
    assert decode_option_ipfs_node(opt.to_cbor_hex()) == opt

def test_multiaddr_roundtrip_bytestring():
    # TODO how to handle the r: thing properly?
    # s = "/ip4/104.131.131.82/tcp/4001/p2p/QmaCpDMGvV2BGHeYERUEnRQAwe3N8SzbUtfsmvsqQLuvuJ"
    s = "/ip4/104.131.131.82/tcp/4001"
    m = coerce_ipfs_multiaddr(s)
    assert isinstance(m, ByteString)
    s2 = ipfs_multiaddr_to_string(m)
    assert s == s2
