import re
from .config import ResolvedTestConfig

def assert_node_logs_match(cfg: ResolvedTestConfig, node_ptn: str, line_ptn: str):
    "Assert at least one line in each matching node's script.log matches `pattern`."
    r1 = re.compile(node_ptn)
    r2 = re.compile(line_ptn)
    tmpdir_path = cfg.tmpdir_path()
    log_paths = [
        cfg.script_log_path(name)
        for name in cfg.node_names()
        if r1.match(name)
    ]
    for log_path in log_paths:
        with log_path.open('r') as f:
            lines = [l.rstrip('\n') for l in f.readlines()]
        # print(f'lines: {lines}')
        # print(f'r2: {r2}')
        # print(f'r2.pattern: {r2.pattern}')
        assert any(r2.search(l) for l in lines), f"{log_path} had no line matching {r2.pattern!r}"

def assert_node_logs_do_not_match(cfg: ResolvedTestConfig, node_ptn: str, line_ptn: str):
    "Assert no line in any matching node's script.log matches `pattern`."
    r1 = re.compile(node_ptn)
    r2 = re.compile(line_ptn)
    tmpdir_path = cfg.tmpdir_path()
    log_paths = [
        cfg.script_log_path(name)
        for name in cfg.node_names()
        if r1.match(name)
    ]
    for log_path in log_paths:
        with log_path.open('r') as f:
            lines = [l.rstrip('\n') for l in f.readlines()]
        match = next((l for l in lines if r2.search(l)), None)
        assert match is None, f"{log_path} matched {r2.pattern!r}: {match!r}"
