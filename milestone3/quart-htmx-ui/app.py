import flask

def get_log_entries(query=None):
    return []

def get_state_tree():
    pass

def get_current_role():
    return 'observer'

def get_actions_for_role(role='observer'):
    return []

app = flask.Flask(__name__)

@app.get("/log")
async def log_fragment():
    entries = await get_log_entries()  # from chain
    return await render_template("partials/log.html", entries=entries)

@app.get("/state")
async def state_fragment():
    state = await get_state_tree()  # server-side parse of chain
    return await render_template("partials/state_tree.html", node=state)

@app.get("/filter")
async def filtered_fragments():
    q = request.args.get("q", "").strip()
    log_entries = await get_log_entries(query=q)
    state = await get_state_tree(query=q)

    # Return two fragments stitched together
    return await render_template(
        "partials/filter_result.html",
        entries=log_entries,
        state=state,
    )

@app.get("/actions")
async def actions_fragment():
    role = await get_current_role()  # "observer", "voter", "admin", "guardian"
    actions = get_actions_for_role(role)
    return await render_template("partials/actions.html", actions=actions, role=role)

@app.get("/actions/<action_id>/form")
async def action_form(action_id):
    form = build_form_for_action(action_id)
    return await render_template("partials/modal_form.html", form=form)

@app.post("/actions/<action_id>")
async def submit_action(action_id):
    data = await request.form
    result = await perform_action(action_id, data)

    # Close modal and maybe show a toast/status
    return await render_template("partials/modal_result.html", result=result)

async def main():
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    config.workers = 1 # TODO remove for production?
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())
