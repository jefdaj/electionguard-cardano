import pytest
from pycardano import *
from egc import *
from helpers import global_fixture
import logging

from .static_records import *
# from .static_records import STATIC_RECORDS, STATIC_PHASES, load_static_record_pair, load_static_record_pairs

LOG = logging.getLogger(__name__)

# TODO remove?
@global_fixture
def static_phases():
    return STATIC_PHASES

@global_fixture
def static_transactions():
    return STATIC_TRANSACTIONS

@global_fixture
def subchannel_ids(static_transactions) -> list[ChannelId]:
    return static_transactions['admin'][2][0].channels

@global_fixture
def subchannel_strs(subchannel_ids: list[ChannelId]) -> list[str]:
    return [channel_id_to_string(i) for i in subchannel_ids]

@global_fixture
def static_records_list(static_transactions) -> list[PublicRecord]:
    records = []
    for tx_dict in static_transactions.values():
        for (_, recs) in tx_dict.values():
            records += recs
    return records
