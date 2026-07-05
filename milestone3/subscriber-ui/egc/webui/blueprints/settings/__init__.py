from quart import Blueprint, render_template
from egc.core import Entry, get_log_entries, get_state_tree

bp = Blueprint("settings", __name__, template_folder="templates")

@bp.route("/")
async def index():
    return await render_template("index.html")


