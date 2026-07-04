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
    sub_cfg = SubscriberConfig(since_slot='116458744',
                 since_block_hash='7c5bd72816b5e61e7814f3c385305ffc48411ab27ff2a0771d2cfae69af23943',
                 policy_id=ScriptHash(bytes.fromhex('b8627e36b5434a5102f690785e1f22ae95093aef2d400a7cbcbb0b89')))

    @app.before_serving
    async def startup():
        app.subscriber = ElectionSubscriber(sub_cfg) # TODO on_action
        app.subscriber.start()

    @app.after_serving
    async def shutdown():
        app.subscriber.stop()

    return app
