from egc import save_qrcode
from pathlib import Path
from ..config import ResolvedTestConfig

QR_STRS_PATH = Path(__file__).parent / 'elections.txt'
QR_STRS = QR_STRS_PATH.read_text().splitlines()

def install_qr_txt(cfg: ResolvedTestConfig, drawn: int):
    """Write a random election qr str in the qrcodes dir.
    `drawn` as a generic int prevents having to export `QR_STRS`."""
    qr_idx = drawn % len(QR_STRS)
    qr_str = QR_STRS[qr_idx]
    qr_path = cfg.qrcodes_path() / 'election.txt'
    qr_path.write_text(qr_str)

def install_qr_png(cfg: ResolvedTestConfig, drawn: int):
    """Write a random election qrcode png in the qrcodes dir.
    `drawn` as a generic int prevents having to export `QR_STRS`."""
    qr_idx = drawn % len(QR_STRS)
    qr_str = QR_STRS[qr_idx]
    qr_path = cfg.qrcodes_path() / 'election.png' # TODO svg?
    save_qrcode(obj=qr_str, path=qr_path)
