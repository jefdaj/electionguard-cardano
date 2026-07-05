import hashlib
from quart import Blueprint, render_template, request, current_app
from typing import Optional

bp = Blueprint("history", __name__, template_folder="templates")

@bp.route("/")
async def index():
    return await render_template("index.html")

def version_including_filter(sub_version: str, filter_str: Optional[str]):
    if filter_str:
        filter_version = hashlib.md5(filter_str.encode()).hexdigest()[:8]
        return f'{filter_version}:{sub_version}'
    else:
        return sub_version

def build_tree(filter_str=None):
    tree = {"label": "Election", "children": [
        {"label": "Key ceremony", "children": [
            {"label": "Round 1", "children": []},
        ]},
        {"label": "Voting", "children": []},
    ]}
    # apply filter_str here later
    return tree


def get_history_filter() -> Optional[str]:
    return request.args.get("history-filter", "").strip() or None


# This isn't technically needed, but helps with debugging.
@bp.route("/tree")
async def tree():
    filter_str = get_history_filter()
    return await render_template(
        "history/partials/tree.html",
        tree=build_tree(filter_str=filter_str)
    )


# Because we want to filter both the log and tree at once, we return the two
# divs wrapped in filter_result. Then each is swapped with its correct div
# client side using hx-swap-oob.
# TODO rename something like events? if it's also rendering by polling for changes
@bp.get("/filter")
async def filter_results():
    filter_str = get_history_filter()

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
        events=events,
        tree=build_tree(filter_str=filter_str),
        history_ver=cur_ver,
    )


