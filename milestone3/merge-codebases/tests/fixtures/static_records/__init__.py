import json
from pathlib import Path

from tests.helpers import global_fixture

from .generated import STATIC_PHASES
from .generated import STATIC_TRANSACTIONS

import logging
LOG = logging.getLogger(__name__)

from egc import *

STATIC_FILES_DIR = Path(__file__).absolute().parent / 'files'

@global_fixture
def static_files_dir():
    return STATIC_FILES_DIR

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

# @global_fixture
# def static_record_pairs(static_records_list: list[PublicRecord], static_files_dir):
#     return load_static_record_pairs(static_records_list, static_files_dir)
