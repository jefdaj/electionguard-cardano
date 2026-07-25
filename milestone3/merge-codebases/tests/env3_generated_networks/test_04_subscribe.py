import pytest
import sys
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace

# weird wrapping just adds to the test!
OLD_QR_STRS = [

  # '''egc:election:3:d8799f5820dd0cae35b7b285c763543ac48f9a17334389705421
  # 1abd51cc00591958467f2102ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz
  # 8605yea78hgyg6uckjakk5:118279331:8bc5402b2f2db94ad2f6ae01506d141558cc4
  # 32e60873549cb9242e1d40b7a13''',

  # '''egc:election:3:d8799f5820fa655ccdddf7e
  # eecc80dd21cb575d9a3e6d07a96188788cf09adfdbde6
  # 7e565000ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2
  # xz8605yea78hgyg6uckjakk5:118279418:5f2d1e4137b870aad05562
  # cafc6ece00cd06d1dd6c968b1490bdaf3badbca430''',

  # '''egc:election:3:d8799f5820c1a3b60b14902823663a88602549d0
  # 71558833fa93ad61fe2a01f424dff19f1c00ff:2
  # :addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6uckjakk5:
  # 118279549:d658626596b91538146078
  # d4fd69c332bc1b638fbfcadb47ed3237f2ee2b1d5b''',

  # '''egc:
  # election:
  # 3:
  # d8799f58207db31e039d39a82598e8b3d9c9b35f771a0789f974a0
  # e7ad85b7e2cfb6dd2d8600ff:2
  # :addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea7
  # 8hgyg6uckjakk5:118279709:69bac2384a55c72cb72123
  # 87e77101608bb7ba2189beb22e35e0168003d05931''',

  '''egc:election:3:d8799f582044868d8028d85581
  bc2f9f0d8887fe50fbc937a0abc1afb5ca2e8f8dcdba
  c01600ff:2:addr_
  test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6uck
  jakk5:118279899:156914063b8ea786ba55
  764cc5c77b4b0ecf301789cd24a3ed9a2a0d3129ca36


  ''',

]

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
    max_examples   = 1,
)
def test_subscribe_old_qr_str(cfg: ResolvedTestConfig):
    # assert_node_logs_match(cfg=cfg, pattern='^\\s*"addr": "addr_test1')
    pass
