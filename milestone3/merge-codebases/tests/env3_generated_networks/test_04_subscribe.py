import pytest
import sys
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace

OLD_QR_STRS = [

    # TODO add back a max blocks to wait before calling an election done

    # init_election only
    # '''egc:election:3:d8799f5820be3f80b1c83cc2445fae4b2157a4bcf34f5a4b6d5e032f1deedb3
    # f067dffdf6400ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6uckjak
    # k5:118296189:11b99ea65fd54e194dc32fb4fbb4b76402175c24fab997db2e8861513be9c113''',

    # happy_subchannels
    # '''egc:election:3:d8799f5820b2106681301173bebf1568dffde6e8bdf5b76517e51d17b527370
    # ccb3ed14e2500ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6uckjak
    # k5:118296353:5a2e81d54ad3efb5da12f46cea5fb4f22e26e09e5a5b6b18336e148236146ec0''',

    # happy_election
    '''egc:election:3:d8799f5820c81cf66e6e2c118f96d1e9b064b693d6def8a451e8b030372dd69
    c172a90c9e800ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6uckjak
    k5:118296546:b23e0378ce52c791f9c449be3f1f44ab3a79be15adb309ccfb9751ab5f2f8392''',

]

# TODO wait, does this also need to be hashed??
# TODO how to make these easier to debug?
@st.composite
def setup_old_qr_str(draw):
    print('running setup_old_qr_str')
    i = draw(st.integers(0, len(OLD_QR_STRS)))
    qr_str = OLD_QR_STRS[i]
    def write_qr_str(cfg: ResolvedTestConfig):
        print('runnin write_qr_str')
        for node_name in cfg.node_names():
            private_dir = cfg.egc_private_dir_path(node_name)
            qr_path = private_dir / 'qr-str.txt'
            qr_path.write_text(qr_str)
            assert qr_path.exists()
    return write_qr_str

@st.composite
def subscribe_old_qr_str_config(draw):
    cfg = draw( hashed_test_config() )
    cfg = replace(cfg, cfg_type = sys._getframe().f_code.co_name)
    for nodes in ['admin', 'guardians', 'devices', 'verifiers']:
        attr_path = f'nodes.{nodes}.template'
        cfg = deep_replace(cfg, attr_path, 'subscribe.sh')
    return cfg

@given_cached_tests(
    cfg_strategy   = subscribe_old_qr_str_config,
    setup_strategy = setup_old_qr_str,
    max_examples   = 3,
)
def test_subscribe_old_qr_str(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^ElectionEvent.*ended election')
