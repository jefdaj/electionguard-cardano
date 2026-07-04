from quart import Quart, Config
from quart import render_template, request

# TODO remove pycardano.hash from core exports to avoid shadowing system one
# from ..core import Entry, get_log_entries, get_state_tree

from ..core import ElectionSubscriber, SubscriberConfig
from pycardano import ScriptHash

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

    # TODO get somehow rather than hardcoding
    sub_cfg = SubscriberConfig(since_slot='116475398',
                 since_block_hash='19d0a4a1c9027fa2a4babe7c02eb88441f9ce7e952d3cdcf20bae29edbe87947',
                 policy_id=ScriptHash(bytes.fromhex('9ea1e52c2a65e5b8fb49ea8990816c4a1cff67f3d2360c53d1843159')))

    @app.before_serving
    async def startup():
        app.subscriber = ElectionSubscriber(sub_cfg) # TODO on_action
        app.subscriber.start()

    @app.after_serving
    async def shutdown():
        app.subscriber.stop()

    return app
