from quart import Quart, Config
from quart import render_template, request

# TODO remove pycardano.hash from core exports to avoid shadowing system one
from ..core import Entry, get_log_entries, get_state_tree

def create_app(config=None):
    app = Quart(__name__)  # static_folder/template_folder resolve to package dir
    if config:
        app.config.from_mapping(config)
    # else:

    #     config = Config()
    #     config.bind = ["0.0.0.0:5000"]

        # For production, increase workers based on CPU cores
        # Recommended: (2 * num_cores) + 1
    #     config.workers = 1

    # from .blueprints.main import bp as main_bp
    # app.register_blueprint(main_bp)

    from .blueprints.partials import bp as partials_bp
    app.register_blueprint(partials_bp, url_prefix="/partials")

    # allow hash() to be used in templates
    app.jinja_env.globals.update(hash=hash)

    @app.get("/")
    async def index():
        return await render_template("index.html")

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

    return app

