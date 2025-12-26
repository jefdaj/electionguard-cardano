#!/usr/bin/env python3

import os
import threading
import time
from typing import List

from flask import Flask, jsonify, render_template_string, request
import ipfshttpclient
import requests


IPFS_API_ADDR = os.getenv("IPFS_API_ADDR", "/ip4/127.0.0.1/tcp/5001")
CID_PROVIDER_URL = os.getenv("CID_PROVIDER_URL", "http://localhost:8080/cids")
CID_POLL_INTERVAL = float(os.getenv("CID_POLL_INTERVAL", "30.0"))

app = Flask(__name__)

# Global state for demo purposes; in real apps use something more robust.
state = {
    "pinned_cids": set(),
    "last_sync": None,
    "sync_errors": [],
}


def fetch_cids_from_provider() -> List[str]:
    """
    Fetch a list of CIDs from an external service.
    Expected response: JSON list of strings, e.g. ["Qm...", "bafy..."].
    """
    resp = requests.get(CID_PROVIDER_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError("CID provider must return a JSON list")
    return [str(cid).strip() for cid in data if cid]


def pin_cid(client: ipfshttpclient.Client, cid: str) -> None:
    app.logger.info(f"Pinning CID: {cid}")
    client.pin.add(cid)


def ipfs_sync_loop():
    """
    Background loop that periodically fetches CIDs and pins them.
    """
    app.logger.info("Starting IPFS sync loop")
    client = ipfshttpclient.connect(addr=IPFS_API_ADDR)

    while True:
        try:
            cids = fetch_cids_from_provider()
            new_cids = [cid for cid in cids if cid not in state["pinned_cids"]]

            for cid in new_cids:
                try:
                    pin_cid(client, cid)
                    state["pinned_cids"].add(cid)
                except Exception as e:
                    msg = f"Error pinning {cid}: {e}"
                    app.logger.error(msg)
                    state["sync_errors"].append(msg)

            state["last_sync"] = time.time()
        except Exception as e:
            msg = f"Sync error: {e}"
            app.logger.error(msg)
            state["sync_errors"].append(msg)

        time.sleep(CID_POLL_INTERVAL)


# ----------------- Flask routes ----------------- #

INDEX_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Flask + htmx + IPFS</title>
  <!-- htmx from CDN; you can vendor it if you prefer -->
  <script src="https://unpkg.com/htmx.org@1.9.12"></script>
</head>
<body>
  <h1>IPFS Sync Status</h1>

  <button
    hx-get="/api/status"
    hx-target="#status"
    hx-swap="innerHTML">
    Refresh Status
  </button>

  <div id="status">
    <!-- Initial content -->
    <p>Status not loaded yet. Click "Refresh Status".</p>
  </div>

  <h2>Pin CID Manually</h2>
  <form
    hx-post="/api/pin"
    hx-target="#pin-result"
    hx-swap="innerHTML">
    <input type="text" name="cid" placeholder="Enter CID" required />
    <button type="submit">Pin</button>
  </form>

  <div id="pin-result"></div>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_TEMPLATE)


@app.route("/api/status")
def status():
    return jsonify(
        pinned_cids=sorted(list(state["pinned_cids"])),
        last_sync=state["last_sync"],
        sync_errors=state["sync_errors"][-10:],  # last 10 errors
    )


@app.route("/api/pin", methods=["POST"])
def api_pin():
    cid = request.form.get("cid") or request.json.get("cid") if request.is_json else None
    if not cid:
        return ("Missing 'cid'", 400)

    try:
        client = ipfshttpclient.connect(addr=IPFS_API_ADDR)
        pin_cid(client, cid)
        state["pinned_cids"].add(cid)
    except Exception as e:
        app.logger.error(f"Manual pin error for {cid}: {e}")
        return (f"Error pinning {cid}: {e}", 500)

    # For htmx, return HTML snippet, but also reasonable for plain browser.
    return f"<p>Pinned CID: <code>{cid}</code></p>"


def start_background_thread():
    t = threading.Thread(target=ipfs_sync_loop, daemon=True)
    t.start()


if __name__ == "__main__":
    # Start background sync thread, then run Flask dev server
    start_background_thread()
    app.run(host="0.0.0.0", port=5000, debug=True)
