import io
import os
import qrcode
import subprocess
from typing import Any
import sys
import cv2
import time
from pprint import pprint


def is_linux_dark_mode() -> bool:

    # GNOME / GTK (most common)
    try:
        out = subprocess.check_output(
            ['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'],
            stderr=subprocess.DEVNULL, text=True
        ).strip().strip("'")
        if out in ('prefer-dark', 'prefer-light'):
            return out == 'prefer-dark'
        if out == 'default':
            return False
    except Exception:
        pass

    # KDE Plasma
    # TODO test this
    try:
        out = subprocess.check_output(
            ['kreadconfig5', '--group', 'General', '--key', 'ColorScheme'],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        return 'dark' in out.lower()
    except Exception:
        pass

    # Fallback: COLORFGBG env var (set by some terminals, e.g. rxvt)
    # Format is "fg;bg" — bg < 8 usually means dark
    # TODO test this
    colorfgbg = os.environ.get('COLORFGBG', '')
    if colorfgbg:
        try:
            return int(colorfgbg.split(';')[-1]) < 8
        except ValueError:
            pass

    return True # assume dark if unknown


def print_qrcode(obj: Any) -> None:
    "Print a QR code with wrapped text below."
    # TODO is there a cleaner way?

    # encode obj
    if hasattr(obj, 'to_qrcode'):
        qr = obj.to_qrcode()
    else:
        # TODO raise error here?
        qr = str(obj) # TODO repr instead? or json.dumps?
        qr = qrcode.QRCode(txt)
        qr.make()

    # save to a buffer so we can get width
    buf = io.StringIO()
    qr.print_ascii(out=buf, invert=is_linux_dark_mode())
    qr_lines = buf.getvalue().splitlines()
    qr_width = len(qr_lines[0]) - (2 * qr.border)

    # print code with wrapped text below
    print('\n'.join(qr_lines[:-1]))
    txt = b''.join(d.data for d in qr.data_list).decode('utf-8')
    lines_printed = 0
    while True:
        start = lines_printed * qr_width
        end = start + qr_width
        print(' ' * qr.border + txt[start:end] + ' ' * qr.border)
        lines_printed += 1
        if end > len(txt):
            break
    print()


def scan_qrcode(decode_cls=None, video_device=0, timeout=0):
    "Scan a QR Code and optionally decode it using from_qr_str."
    cap = cv2.VideoCapture(video_device)
    if not cap.isOpened():
        raise Exception(f"Cannot open video device {video_device!r}")
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1) # enable autofocus
    det = cv2.QRCodeDetector()
    start = time.time()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.1) # TODO remove?
                continue
            data, pts, _ = det.detectAndDecode(frame)
            if data:
                try:
                    return decode_cls.from_qr_str(data)
                except:
                    # TODO raise error here?
                    return data
            if timeout and time.time() - start > timeout:
                raise TimeoutError
    finally:
        cap.release()

if __name__ == "__main__":
    main()
