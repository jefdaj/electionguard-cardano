from quart import Blueprint, render_template, request, current_app
from egc.core import Entry, get_log_entries, get_state_tree

bp = Blueprint("history", __name__, template_folder="templates")

@bp.route("/")
async def index():
    return await render_template("index.html")

# Because we want to filter both the log and tree at once, we return the two
# divs wrapped in filter_result. Then each is swapped with its correct div
# client side using hx-swap-oob.
# TODO does specifying hx-swap-oob in the returned html like this work?
# TODO rename something like events? if it's also rendering by polling for changes
@bp.get("/filter")
async def filter_results():

    # return 204 (no new content) if polling and the version hasn't changed
    req_ver = request.headers.get("HX-Trigger-Version")
    is_poll = req_ver is not None # to avoid 204 when explicitly filtering
    cur_ver = current_app.subscriber.version()
    if is_poll and cur_ver == req_ver:
        return "", 204 # unchanged; htmx skips the swap

    q = request.args.get("history-filter", "").strip() # TODO would "query" be more standard?
    events = current_app.subscriber.all_events()

    # TODO factor out into something more general
    if len(q.lower()) > 0:
        events = [e for e in events if q.lower() in str(e).lower()]

    tree = get_state_tree(query=q)
    return await render_template(
        "history/partials/filter_results.html",
        events=events,
        tree=tree,
        history_ver=cur_ver,
    )


