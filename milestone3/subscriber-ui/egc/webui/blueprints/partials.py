from quart import Blueprint, render_template

bp = Blueprint("partials", __name__)

@bp.route("/log")
async def log_fragment():
    entries = get_log_entries()
    return await render_template("partials/log.html", entries=entries)

