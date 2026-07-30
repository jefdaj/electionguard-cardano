import re
from .config import ResolvedTestConfig

def assert_node_logs_match(cfg: ResolvedTestConfig, pattern: str):
    "Assert at least one line in each node's script.log matches `pattern`."
    rx = re.compile(pattern)
    tmpdir_path = cfg.tmpdir_path()
    log_paths = [
        cfg.script_log_path(name)
        for name in cfg.node_names()
    ]
    for log_path in log_paths:
        with log_path.open('r') as f:
            lines = [l.rstrip('\n') for l in f.readlines()]
        # print(f'lines: {lines}')
        # print(f'rx: {rx}')
        # print(f'rx.pattern: {rx.pattern}')
        assert any(rx.search(l) for l in lines), f"{log_path} had no line matching {rx.pattern!r}"

def assert_node_logs_do_not_match(cfg: ResolvedTestConfig, pattern: str):
    "Assert no line in any node's script.log matches `pattern`."
    rx = re.compile(pattern)
    tmpdir_path = cfg.tmpdir_path()
    log_paths = [
        cfg.script_log_path(name)
        for name in cfg.node_names()
    ]
    for log_path in log_paths:
        with log_path.open('r') as f:
            lines = [l.rstrip('\n') for l in f.readlines()]
        match = next((l for l in lines if rx.search(l)), None)
        assert match is None, f"{log_path} matched {rx.pattern!r}: {match!r}"
