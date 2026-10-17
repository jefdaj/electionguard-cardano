import os
import shutil
from pathlib import Path
from ..config import ResolvedTestConfig

def install_funder_sk(cfg: ResolvedTestConfig):
    "Copy ./keys/dev.sk -> admin private dir for use in init_election."
    host_keys_dir  = Path(os.environ.get('EGC_WALLET_DIR', 'keys')) # TODO better default?
    admin_keys_dir = cfg.private_path('admin') / 'egc'
    host_sk_path   = host_keys_dir  / 'dev.sk'
    admin_sk_path  = admin_keys_dir / 'funder.sk'
    admin_keys_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(host_sk_path, admin_sk_path)
