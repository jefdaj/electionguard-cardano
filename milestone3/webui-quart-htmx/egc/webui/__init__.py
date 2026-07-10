import os

from quart import Quart, Config
from quart import render_template, request

# TODO remove pycardano.hash from core exports to avoid shadowing system one

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

    from .blueprints.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix="/settings")

    # allow hash() to be used in templates
    app.jinja_env.globals.update(hash=hash)

    (policy_id, slot_no, header_hash) = os.environ['SUBSCRIBE_ARGS'].split(' ')[:3]
    sub_cfg = SubscriberConfig(since_slot=int(slot_no),
                 since_block_hash=header_hash,
                 policy_id=ScriptHash(bytes.fromhex(policy_id)))

    @app.before_serving
    async def startup():
        app.subscriber = ElectionSubscriber(sub_cfg) # TODO on_action
        app.subscriber.start()

    @app.after_serving
    async def shutdown():
        app.subscriber.stop()

    return app
