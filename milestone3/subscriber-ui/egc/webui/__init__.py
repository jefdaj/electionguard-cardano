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

    from .blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)

    from .blueprints.history import bp as history_bp
    app.register_blueprint(history_bp, url_prefix="/history")

    # allow hash() to be used in templates
    app.jinja_env.globals.update(hash=hash)

    return app
