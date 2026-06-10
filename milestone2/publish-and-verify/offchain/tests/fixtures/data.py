import pytest
from pycardano import *
from egc import *
from data.static_records import *
from test_utils import per_election_fixture
import logging

LOG = logging.getLogger(__name__)

@per_election_fixture
def static_phases():
    return STATIC_PHASES

@per_election_fixture
def static_transactions():
    return STATIC_TRANSACTIONS

@per_election_fixture
def static_files_by_cid() -> dict[str, Path]:
    return STATIC_FILES_BY_CID

@per_election_fixture
def subchannel_ids(static_transactions) -> list[ChannelId]:
    return static_transactions['admin'][2][0].channels

@per_election_fixture
def subchannel_strs(subchannel_ids: list[ChannelId]) -> list[str]:
    return [ChannelIdHelper.to_string(i) for i in subchannel_ids]


