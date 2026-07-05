import hashlib
from quart import Blueprint, render_template, request, current_app
from typing import Optional

bp = Blueprint("history", __name__, template_folder="templates")


### index ###


@bp.route("/")
async def index():
    return await render_template("index.html")

def version_including_filter(sub_version: str, filter_str: Optional[str]):
    if filter_str:
        filter_version = hashlib.md5(filter_str.encode()).hexdigest()[:8]
        return f'{filter_version}:{sub_version}'
    else:
        return sub_version


### tree ###


def build_tree(filter_str=None):
    return {"id": "election", "label": "Election", "children": [
        {"id": "key", "label": "Key ceremony", "children": [
            {"id": "key-r1", "label": "Round 1", "children": []},
        ]},
        {"id": "voting", "label": "Voting", "children": []},
    ]}


def get_history_filter() -> Optional[str]:
    return request.args.get("history-filter", "").strip() or None

def get_open_ids() -> set[str]:
    return set(filter(None, request.args.get("open", "").split(",")))


def node_matches(node, f):
    return f is None or f.lower() in str(node["label"]).lower()

def visible(node, f):
    if f is None:
        return True
    return node_matches(node, f) or any(visible(c, f) for c in node["children"])

def has_visible_child(node, f):
    return any(visible(c, f) for c in node["children"])

def is_open(node, open_ids, f):
    if f is not None and has_visible_child(node, f):
        return True          # force-open ancestors of matches
    return node["id"] in open_ids

def toggle_ids(open_ids, node_id):
    s = set(open_ids)
    s.discard(node_id) if node_id in s else s.add(node_id)
    return ",".join(sorted(s))   # canonical, stable URLs


@bp.before_app_serving
async def register_globals():
    current_app.jinja_env.globals.update(
        visible=visible, is_open=is_open, toggle_ids=toggle_ids,
    )


# This isn't technically needed, but helps with debugging.
@bp.route("/tree")
async def tree():
    filter_str = get_history_filter()
    open_ids = get_open_ids()
    return await render_template(
        "history/partials/tree.html",
        tree=build_tree(filter_str), open_ids=open_ids, filter_str=filter_str,
    )


### filter_results ###


# Because we want to filter both the log and tree at once, we return the two
# divs wrapped in filter_result. Then each is swapped with its correct div
# client side using hx-swap-oob.
# TODO rename something like events? if it's also rendering by polling for changes
@bp.get("/filter")
async def filter_results():
    filter_str = get_history_filter()
    open_ids = get_open_ids()

    # return 204 (no new content) if polling and the version hasn't changed
    req_ver = request.headers.get("HX-Trigger-Version")
    cur_ver = version_including_filter(current_app.subscriber.version(), filter_str)
    if cur_ver == req_ver:
        return "", 204 # unchanged; htmx skips the swap

    events = current_app.subscriber.all_election_events()

    if filter_str:
        events = [e for e in events if filter_str.lower() in str(e).lower()]

    return await render_template(
        "history/partials/filter_results.html",
        events=events, tree=build_tree(filter_str),
        open_ids=open_ids, filter_str=filter_str, history_ver=cur_ver,
    )
