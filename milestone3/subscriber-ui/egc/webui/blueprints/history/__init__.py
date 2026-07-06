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
    # Note that the root node isn't currently shown. So no point having a root.html template.
    return {"id": "election", "type": "root", "label": "Election", "children": [
        {"id": "key", "type": "key_ceremony", "label": "Key ceremony", "children": [
            {"id": "key-r1", "type": "key_round", "round": 1, "done": 2, "total": 3, "children": []},
        ]},
        {"id": "voting", "type": "voting", "submitted": 25, "children": []},
    ]}

def get_history_filter() -> Optional[str]:
    return request.args.get("history-filter", "").strip() or None

def get_open_ids() -> set[str]:
    return set(filter(None, request.args.get("open", "").split(",")))

def get_closed_ids() -> set[str]:
    return set(filter(None, request.args.get("closed", "").split(",")))

def node_matches(node, f):
    return f is None or f.lower() in str(node).lower()

def visible(node, f):
    if f is None:
        return True
    return node_matches(node, f) or any(visible(c, f) for c in node["children"])

def has_visible_child(node, f):
    return any(visible(c, f) for c in node["children"])

def is_open(node, open_ids, closed_ids, f):
    if node["id"] in closed_ids:
        return False                      # explicit user collapse always wins
    if f is not None and has_visible_child(node, f):
        return True                       # filter force-open
    return node["id"] in open_ids

def toggle_ids(open_ids, closed_ids, node_id, currently_open):
    o, c = set(open_ids), set(closed_ids)
    if currently_open:                    # user is collapsing it
        o.discard(node_id); c.add(node_id)
    else:                                 # user is expanding it
        c.discard(node_id); o.add(node_id)
    return ",".join(sorted(o)), ",".join(sorted(c))


@bp.before_app_serving
async def register_globals():
    current_app.jinja_env.globals.update(
        visible=visible, is_open=is_open, toggle_ids=toggle_ids,
    )


# This isn't technically needed, but helps with debugging.
@bp.route("/tree")
async def tree():
    filter_str = get_history_filter()
    open_ids   = get_open_ids()
    closed_ids = get_closed_ids()
	# If loading the tree as a standalone page (for debugging),
	# need to add the HTMX script to it.
    template = (
        "history/partials/tree.html" if request.headers.get("HX-Request")
        else "history/tree_page.html"
    )
    return await render_template(
        template,
        tree=build_tree(filter_str),
        open_ids=open_ids, closed_ids=closed_ids,
        filter_str=filter_str,
    )


### filter_results ###


# Because we want to filter both the log and tree at once, we return the two
# divs wrapped in filter_result. Then each is swapped with its correct div
# client side using hx-swap-oob.
# TODO rename something like events? if it's also rendering by polling for changes
@bp.get("/filter")
async def filter_results():
    filter_str = get_history_filter()
    open_ids   = get_open_ids()
    closed_ids = get_closed_ids()

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
        open_ids=open_ids, closed_ids=closed_ids,
        filter_str=filter_str, history_ver=cur_ver,
    )
