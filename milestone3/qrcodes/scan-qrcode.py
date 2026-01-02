#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python3 zbar

# Usage: ./scan-qrcode.py
# It will print the text of the first code it sees to stdout and exit.

import subprocess
import threading
import time
import sys


def scan_qr(inactivity_timeout=1.0, max_total_time=30.0):
    lines = []
    last_data_time = None
    first_data_time = None
    lock = threading.Lock()

    process = subprocess.Popen(
        ['zbarcam', '--raw'],
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def reader():
        nonlocal last_data_time, first_data_time
        for line in process.stdout:
            if not line:
                break
            line = line.rstrip('\n')
            now = time.monotonic()
            with lock:
                if first_data_time is None:
                    first_data_time = now
                last_data_time = now
                lines.append(line)

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    start_time = time.monotonic()
    try:
        while True:
            now = time.monotonic()
            if now - start_time > max_total_time:
                break

            with lock:
                ldt = last_data_time

            if ldt is not None and now - ldt >= inactivity_timeout:
                # No new data for inactivity_timeout seconds
                break

            # Slight sleep to avoid busy loop
            time.sleep(0.05)
    finally:
        try:
            process.terminate()
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    t.join(timeout=1)
    return "\n".join(lines)


if __name__ == "__main__":
    text = scan_qr()
    if text:
        print(text)
    else:
        print("No QR data read", file=sys.stderr)

