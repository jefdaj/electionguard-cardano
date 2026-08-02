import re
from .config import ResolvedTestConfig

def _assert_logs(cfg, node_ptn, line_ptn, path_getter, *, should_match):
    r1, r2 = re.compile(node_ptn), re.compile(line_ptn)
    log_paths = [
        path_getter(name)
        for name in cfg.node_names()
        if r1.match(name)
    ]
    for log_path in log_paths:
        with log_path.open('r') as f:
            lines = [l.rstrip('\n') for l in f]
        match = next((l for l in lines if r2.search(l)), None)
        if should_match:
            assert match is not None, \
                f"{log_path} had no line matching {r2.pattern!r}"
        else:
            assert match is None, \
                f"{log_path} matched {r2.pattern!r}: {match!r}"

def assert_node_logs_match(cfg, node_ptn, line_ptn):
    _assert_logs(cfg, node_ptn, line_ptn, cfg.node_log_path, should_match=True)

def assert_script_logs_match(cfg, node_ptn, line_ptn):
    _assert_logs(cfg, node_ptn, line_ptn, cfg.script_log_path, should_match=True)

def assert_node_logs_do_not_match(cfg, node_ptn, line_ptn):
    _assert_logs(cfg, node_ptn, line_ptn, cfg.node_log_path, should_match=False)

def assert_script_logs_do_not_match(cfg, node_ptn, line_ptn):
    _assert_logs(cfg, node_ptn, line_ptn, cfg.script_log_path, should_match=False)
