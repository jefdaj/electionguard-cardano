from quart import Blueprint, render_template

bp = Blueprint("main", __name__)

@bp.get("/")
async def index():
    return await render_template("index.html")
