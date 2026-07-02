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


