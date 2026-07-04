from quart import Blueprint, render_template, request
from egc.core import Entry, get_log_entries, get_state_tree

bp = Blueprint("history", __name__, template_folder="templates")

@bp.route("/")
async def index():
    return await render_template("index.html")

# Because we want to filter both the log and tree at once, we return the two
# divs wrapped in filter_result. Then each is swapped with its correct div
# client side using hx-swap-oob.
# TODO does specifying hx-swap-oob in the returned html like this work?
@bp.get("/filter")
async def filter_results():
    q = request.args.get("history-filter", "").strip() # TODO would "query" be more standard?
    log_entries = get_log_entries(query=q)
    tree = get_state_tree(query=q)
    return await render_template(
        "history/partials/filter_results.html",
        entries=log_entries,
        tree=tree,
    )


