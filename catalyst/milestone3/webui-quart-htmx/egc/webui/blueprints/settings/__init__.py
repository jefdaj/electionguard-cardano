from quart import Blueprint, render_template

bp = Blueprint("settings", __name__, template_folder="templates")

@bp.route("/")
async def index():
    return await render_template("index.html")


