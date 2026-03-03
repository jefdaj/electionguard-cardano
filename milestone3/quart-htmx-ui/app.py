from quart import Quart
from quart import render_template, request
from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio

# Query format should match get_state_tree so they can be filtered together.
def get_log_entries(query=None):
    # will come from kupo indexer
    return []

# Query format should match get_log_entries so they can be filtered together.
def get_state_tree(query=None):
    # server-side parse of chain
    return None

app = Quart(__name__)

@app.get("/")
async def index():
    return await render_template("index.html")

@app.get("/log")
async def log_fragment():
    entries = get_log_entries()
    return await render_template("partials/log.html", entries=entries)

@app.get("/state")
async def state_fragment():
    state = get_state_tree()
    return await render_template("partials/state_tree.html", node=state)

# Because we want to filter both the log and tree at once, we return the two
# divs wrapped in filter_result. Then each is swapped with its correct div
# client side using hx-swap-oob.
# TODO does specifying hx-swap-oob in the returned html like this work?
@app.get("/filter")
async def filtered_fragments():
    q = request.args.get("q", "").strip()
    log_entries = get_log_entries(query=q)
    state = get_state_tree(query=q)
    return await render_template(
        "partials/filter_result.html",
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
