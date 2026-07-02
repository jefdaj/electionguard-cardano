from .config     import *
from .ogmios     import *
from .wallet     import *
from .publisher  import ElectionPublisher
from .subscriber import ElectionSubscriber, SubscriberConfig
from .plutus     import *
from .election   import ElectionScript, ElectionDeployment, ElectionContext
from .node       import ElectionNode
from .utils      import safe_deepdiff
from .records    import *
from .ipfs       import *

# TODO remove everything from here down

from dataclasses import dataclass

# Just the example data structure from the previous UI mockup.
# TODO replace with actual egc core

@dataclass
class Entry:
    id: int
    height: int
    type: str
    summary: str
    timestamp: str

ENTRIES = [
    Entry(1, 1, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(2, 4, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(3, 5, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(4, 7, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(5, 10, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(6, 11, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(7, 15, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(8, 16, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(9, 17, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(10, 18, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(11, 18, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(12, 18, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(13, 18, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(14, 20, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(15, 22, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(16, 34, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(17, 35, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(18, 35, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(19, 35, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(20, 40, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(21, 41, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(22, 44, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(23, 45, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(24, 47, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
]

# Query format should match get_state_tree so they can be filtered together.
def get_log_entries(query=None):
    # will come from kupo indexer
    entries = ENTRIES
    if query is None or len(query) == 0:
        return entries
    entries = [e for e in entries if query.lower() in repr(e).lower()]
    # for e in entries:
    #     print(repr(e))
    return entries

# Query format should match get_log_entries so they can be filtered together.
def get_state_tree(query=None):
    # server-side parse of chain
    state: Dict[str, Dict[str, int]] = {}
    for e in get_log_entries(query):
        if not e.type in state:
            state[e.type] = {}
        if not e.summary in state[e.type]:
            state[e.type][e.summary] = 0
        state[e.type][e.summary] += 1
    return state


