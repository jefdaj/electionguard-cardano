import hashlib

from quart import Blueprint, render_template, request, current_app

bp = Blueprint("history", __name__, template_folder="templates")

@bp.route("/")
async def index():
    return await render_template("index.html")

def version_including_filter(sub_version: str, filter_str: str):
    filter_version = hashlib.md5(filter_str.encode()).hexdigest()[:8]
    return f'{filter_version}:{sub_version}'

def build_tree(filter_str=None):
    tree = {"label": "Election", "children": [
        {"label": "Key ceremony", "children": [
            {"label": "Round 1", "children": []},
        ]},
        {"label": "Voting", "children": []},
    ]}
    # apply filter_str here later
    return tree

# This isn't technically needed, but helps with debugging.
@bp.route("/tree")
async def tree():
    q = request.args.get("history-filter", "").strip() or None
    return await render_template(
        "history/partials/tree.html",
        tree=build_tree(filter_str=q)
    )

# Because we want to filter both the log and tree at once, we return the two
# divs wrapped in filter_result. Then each is swapped with its correct div
# client side using hx-swap-oob.
# TODO rename something like events? if it's also rendering by polling for changes
@bp.get("/filter")
async def filter_results():
    # TODO rename filter here? or query elsewhere?
    q = request.args.get("history-filter", "").strip()

    # return 204 (no new content) if polling and the version hasn't changed
    req_ver = request.headers.get("HX-Trigger-Version")
    cur_ver = version_including_filter(current_app.subscriber.version(), q)
    if cur_ver == req_ver:
        return "", 204 # unchanged; htmx skips the swap

    events = current_app.subscriber.all_election_events()

    # TODO factor out into something more general
    if len(q.lower()) > 0:
        events = [e for e in events if q.lower() in str(e).lower()]

    return await render_template(
        "history/partials/filter_results.html",
        events=events,
        tree=build_tree(filter_str=q),
        history_ver=cur_ver,
    )


