from quart import Quart
from quart import render_template, request
from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio

from dataclasses import dataclass
from datetime import datetime
from typing import Dict

@dataclass
class Entry:
    id: int
    height: int
    type: str
    summary: str
    timestamp: str

ENTRIES = [
    Entry(1, 1, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(2, 4, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(3, 5, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(4, 7, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(5, 10, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(6, 11, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(7, 15, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(8, 16, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(9, 17, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(10, 18, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(11, 18, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(12, 18, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(13, 18, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(14, 20, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(15, 22, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(16, 34, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(17, 35, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(18, 35, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
    Entry(19, 35, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(20, 40, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(21, 41, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(22, 44, 'INFO', 'System initialized', '2026-03-03 10:15:23'),
    Entry(23, 45, 'WARNING', 'Low temperature', '2026-03-03 10:18:45'),
    Entry(24, 47, 'WARNING', 'High temperature', '2026-03-03 10:18:45'),
]

# Query format should match get_state_tree so they can be filtered together.
def get_log_entries(query=None):
    # will come from kupo indexer
    entries = ENTRIES
    if query is None or len(query) == 0:
        return entries
    entries = [e for e in entries if query.lower() in repr(e).lower()]
    # for e in entries:
    #     print(repr(e))
    return entries

app = Quart(__name__, static_folder='static', static_url_path='/static')

# allow hash() to be used in templates
app.jinja_env.globals.update(hash=hash)

@app.get("/")
async def index():
    return await render_template("index.html")

@app.get("/log")
async def log_fragment():
    entries = get_log_entries()
    return await render_template("partials/log.html", entries=entries)

# State tree commented because I want to build the log + filter first

# Query format should match get_log_entries so they can be filtered together.
def get_state_tree(query=None):
    # server-side parse of chain
    state: Dict[str, Dict[str, int]] = {}
    for e in get_log_entries(query):
        if not e.type in state:
            state[e.type] = {}
        if not e.summary in state[e.type]:
            state[e.type][e.summary] = 0
        state[e.type][e.summary] += 1
    return state

# @app.get("/state")
async def state_fragment():
    state = get_state_tree()
    return await render_template("partials/state_tree.html", state=state)

# Because we want to filter both the log and tree at once, we return the two
# divs wrapped in filter_result. Then each is swapped with its correct div
# client side using hx-swap-oob.
# TODO does specifying hx-swap-oob in the returned html like this work?
@app.get("/filter")
async def filter_results():
    q = request.args.get("filter", "").strip() # TODO would "query" be more standard?
    log_entries = get_log_entries(query=q)
    state = get_state_tree(query=q)
    return await render_template(
        "partials/filter_results.html",
        entries=log_entries,
        state=state,
    )

# Action code commented because I want to build the observer UI first:

# def get_current_role():
#     return 'observer'

# def get_actions_for_role(role='observer'):
#     return []

# @app.get("/actions")
# async def actions_fragment():
#     role = get_current_role()  # "observer", "voter", "admin", "guardian"
#     actions = get_actions_for_role(role)
#     return render_template("partials/actions.html", actions=actions, role=role)

# @app.get("/actions/<action_id>/form")
# async def action_form(action_id):
#     form = build_form_for_action(action_id)
#     return render_template("partials/modal_form.html", form=form)

# @app.post("/actions/<action_id>")
# async def submit_action(action_id):
#     data = request.form
#     result = perform_action(action_id, data)
# 
#     # Close modal and maybe show a toast/status
#     return render_template("partials/modal_result.html", result=result)

async def main():
    config = Config()
    config.bind = ["0.0.0.0:5000"]

    # For production, increase workers based on CPU cores
    # Recommended: (2 * num_cores) + 1
    config.workers = 1

    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())
