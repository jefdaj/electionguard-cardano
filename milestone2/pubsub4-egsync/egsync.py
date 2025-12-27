#!/usr/bin/env python3

import os
import threading
import time
from typing import List

from flask import Flask, jsonify, render_template_string, request, abort
import ipfshttpclient
import requests

PUBLIC_DIR = '/data'

PUBLIC_RECORDS = {
    'manifest': (
        Manifest,
        '1_config/1_announce',
        '1_manifest'
    ),
    'ceremony_details': (
        CeremonyDetails,
        '1_config/1_announce',
        '2_ceremony'
    ),
    'guardian_pubkey': (
        ElectionPublicKey,
        '1_config/2_ceremony/1_pubkeys',
        '{guardian_id}'
    ),
    'guardian_backup': (
        ElectionPartialKeyBackup,
        '1_config/2_ceremony/2_backups',
        '{guardian_id}_backup_{backup_order}'
    ),
    'guardian_verification': (
        ElectionPartialKeyVerification,
        '1_config/2_ceremony/3_verifications',
        '{guardian_id}_backup_{backup_order}'
    ),
    'joint_key': (
        ElectionJointKey,
        '1_config/3_election',
        'joint_key'
    ),
    'constants': (
        ElectionConstants,
        '1_config/3_election',
        'constants'
    ),
    'context': (
        CiphertextElectionContext,
        '1_config/3_election',
        'context'
    ),
    'device': (
        EncryptionDevice,
        '1_config/4_devices',
        'device_{device_number}'
    ),
    'ballot_submitted': (
        CiphertextBallot, # TODO SubmittedBallot with state set to UNKNOWN?
        '2_ballots/1_submitted',
        '{ballot_id}'
    ),
    'cast_notice': (
        CastNotice,
        '2_ballots/2_cast',
        '{ballot_id}'
    ),
    'ballot_spoiled': (

        # This seems correct to me even though it doesn't match the
        # electionguard-python implementation: we *do* want to publish all
        # the nonces at this step, right? So people can decrypt immediately
        # rather than waiting for the guardians.
        CiphertextBallot,

        '2_ballots/3_spoiled',
        '{ballot_id}'
    ),
    'ciphertext_tally': (
        PublishedCiphertextTally, # TODO CiphertextTally? (the non-"published" version)
        '3_results',
        '1_tally'
    ),
    'tally_share': (
        DecryptionShare,
        '3_results/2_decrypt/1_shares/1_tally',
        'tally_{guardian_id}'
    ),
    'spoiled_share': (
        DecryptionShare,
        '3_results/2_decrypt/1_shares/2_spoiled',
        '{spoiled_id}_{guardian_id}'
    ),
    # TODO rename tally_result?
    'plaintext_tally': (
        PlaintextTally,
        '3_results/2_decrypt/2_combined',
        '1_tally'
    ),
    'spoiled_result': (
        PlaintextTally,
        '3_results/2_decrypt/2_combined/2_spoiled',
        '{ballot_id}'
    ),
    'summary': (
        dict,
        '4_verify',
        '{verifier_id}'
    ),
}

### get record filenames ###

# TODO put public in the name
def record_basename(record_type:str, **fmtargs):
    'So far, only used to simplify verifier summary json keys'
    (_, _, fstr) = PUBLIC_RECORDS[record_type]
    fname = fstr.format(**fmtargs)
    return fname

# you probably want the public/private specialized versions below
def record_path(records_map, root_dir:str, record_type: str, **fmtargs):
    (_, dname, fstr) = records_map[record_type]
    dpath = join(root_dir, dname)
    makedirs(dpath, exist_ok=True) # TODO make the dir here?
    fname = fstr.format(**fmtargs)
    return join(dpath, fname + '.json')


### load and save single files ###

# you probably want the public or private versions below
def to_record(records_map, record_type: str, obj, **fmtargs):
    (_, dname, fstr) = records_map[record_type]
    dpath = join(PUBLIC_DIR, dname)
    makedirs(dpath, exist_ok=True)
    fname = fstr.format(**fmtargs)
    serialize.to_file(obj, fname, dpath)

# you probably want the public or private versions below
# TODO separate into the json part (here) and the typed part (still in util.py?)
def from_record(records_map, record_type: str, **fmtargs):
    (_, dname, fstr) = records_map[record_type]
    dpath = join(PUBLIC_DIR, dname)
    fname = fstr.format(**fmtargs) + '.json'
    fpath = join(dpath, fname)

    # This returns a Python object of the correct type,
    # but for the API we need JSON.
    # TODO have another step for converting the reply to the type
    # return serialize.from_file(rtype, fpath)
    return json.load(fpath)

def to_public_record(, record_type: str, obj, **fmtargs):
    return to_record(PUBLIC_RECORDS, record_type, obj, **fmtargs)

def from_public_record(record_type: str, **fmtargs):
    return from_record(PUBLIC_RECORDS, record_type, **fmtargs)



# IPFS_API_ADDR = os.getenv("IPFS_API_ADDR", "/ip4/127.0.0.1/tcp/5001")
# CID_PROVIDER_URL = os.getenv("CID_PROVIDER_URL", "http://localhost:8080/cids")
# CID_POLL_INTERVAL = float(os.getenv("CID_POLL_INTERVAL", "30.0"))

app = Flask(__name__)

# Global state for demo purposes; in real apps use something more robust.
# state = {
#     "pinned_cids": set(),
#     "last_sync": None,
#     "sync_errors": [],
# }


# def fetch_cids_from_provider() -> List[str]:
#     """
#     Fetch a list of CIDs from an external service.
#     Expected response: JSON list of strings, e.g. ["Qm...", "bafy..."].
#     """
#     resp = requests.get(CID_PROVIDER_URL, timeout=10)
#     resp.raise_for_status()
#     data = resp.json()
#     if not isinstance(data, list):
#         raise ValueError("CID provider must return a JSON list")
#     return [str(cid).strip() for cid in data if cid]


# def pin_cid(client: ipfshttpclient.Client, cid: str) -> None:
#     app.logger.info(f"Pinning CID: {cid}")
#     client.pin.add(cid)


# def ipfs_sync_loop():
#     """
#     Background loop that periodically fetches CIDs and pins them.
#     """
#     app.logger.info("Starting IPFS sync loop")
#     client = ipfshttpclient.connect(addr=IPFS_API_ADDR)
# 
#     while True:
#         try:
#             cids = fetch_cids_from_provider()
#             new_cids = [cid for cid in cids if cid not in state["pinned_cids"]]
# 
#             for cid in new_cids:
#                 try:
#                     pin_cid(client, cid)
#                     state["pinned_cids"].add(cid)
#                 except Exception as e:
#                     msg = f"Error pinning {cid}: {e}"
#                     app.logger.error(msg)
#                     state["sync_errors"].append(msg)
# 
#             state["last_sync"] = time.time()
#         except Exception as e:
#             msg = f"Sync error: {e}"
#             app.logger.error(msg)
#             state["sync_errors"].append(msg)
# 
#         time.sleep(CID_POLL_INTERVAL)


# ----------------- Flask routes ----------------- #

INDEX_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>egsync</title>
  <!-- htmx from CDN; you can vendor it if you prefer -->
  <script src="https://unpkg.com/htmx.org@1.9.12"></script>
</head>
<body>
  <h1>egsync</h1>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_TEMPLATE)


# @app.route("/api/status")
# def status():
#     return jsonify(
#         pinned_cids=sorted(list(state["pinned_cids"])),
#         last_sync=state["last_sync"],
#         sync_errors=state["sync_errors"][-10:],  # last 10 errors
#     )


# @app.route("/api/pin", methods=["POST"])
# def api_pin():
#     cid = request.form.get("cid") or request.json.get("cid") if request.is_json else None
#     if not cid:
#         return ("Missing 'cid'", 400)
# 
#     try:
#         client = ipfshttpclient.connect(addr=IPFS_API_ADDR)
#         pin_cid(client, cid)
#         state["pinned_cids"].add(cid)
#     except Exception as e:
#         app.logger.error(f"Manual pin error for {cid}: {e}")
#         return (f"Error pinning {cid}: {e}", 500)
# 
#     # For htmx, return HTML snippet, but also reasonable for plain browser.
#     return f"<p>Pinned CID: <code>{cid}</code></p>"

# def start_background_thread():
#     t = threading.Thread(target=ipfs_sync_loop, daemon=True)
#     t.start()


# TODO need another step to convery Python type -> JSON on the other end to send to API?
@app.route("/public_records/<record_type>", methods=["POST"])
def save_public_record(record_type):
    # 1. Validate record_type
    if record_type not in PUBLIC_RECORDS:
        abort(404, description="Unknown record_type")

    rtype, _, _ = PUBLIC_RECORDS[record_type]

    # 2. Require JSON
    if not request.is_json:
        abort(400, description="Expected JSON body")

    raw = request.get_json()

    # 3. Convert JSON → Python object using your serialization layer
    # Adjust these helpers to whatever electionguard.serialize actually provides.
    #
    # Possibilities in many codebases:
    #   obj = serialize.from_dict(rtype, raw)
    #   obj = rtype.from_dict(raw)
    #   obj = serialize.object_from_raw(rtype, raw)
    #
    # I'll write this as a placeholder:
    obj = serialize.from_raw(rtype, raw)

    # 4. Extra format args come from query params (guardian_id, ballot_id, etc.)
    fmtargs = request.args.to_dict()

    # 5. Delegate file-writing to your helper
    to_public_record(PUBLIC_DIR, record_type, obj, **fmtargs)

    return "", 204


@app.route("/public_records/<record_type>", methods=["GET"])
def load_public_record(record_type):
    if record_type not in PUBLIC_RECORDS:
        abort(404, description="Unknown record_type")

    rtype, _, _ = PUBLIC_RECORDS[record_type]
    fmtargs = request.args.to_dict()

    try:
        obj = from_public_record(PUBLIC_DIR, record_type, **fmtargs)
    except FileNotFoundError:
        abort(404, description="Record not found")

    # Convert Python object → JSON-serializable structure
    #
    # Again, adapt to your real helpers:
    #   raw = serialize.to_dict(obj)
    #   raw = obj.to_dict()
    # raw = serialize.to_dict(obj)
    # return jsonify(raw)

    raw = serialize.to_raw(obj)
    return raw


if __name__ == "__main__":
    # Start background sync thread, then run Flask dev server
    # start_background_thread()
    app.run(host="0.0.0.0", port=5000, debug=True)
