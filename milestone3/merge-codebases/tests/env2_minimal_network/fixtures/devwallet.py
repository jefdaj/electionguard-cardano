# import pytest
# from pycardano import *
# from egc import *
# import logging
# import time
# from ..lib import fixture_private_dir
# 
# LOG = logging.getLogger(__name__)
# 
# # TODO can it be session scoped but rely on arion?
# @pytest.fixture(scope='session')
# def reset_funder_wallet(env2_arion_network, funder_wallet: Wallet, env2_tmp_root: Path, request) -> FunderNode:
#     node_ = FunderNode(
#         wallet      = funder_wallet,
#         private_dir = fixture_private_dir(env2_tmp_root, request),
#     )
#     LOG.debug(f'funder: {node_}')
#     node_.ipfs.wait_until_stable_sync()
#     try:
#         yield node_
#         # no need to return collateral to self
#     finally:
#         node_.stop()
