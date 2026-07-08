from quart import Quart, Config

# just to check that it works for now:
from egc import *

import logging

LOG = logging.getLogger(__name__)

def create_app(config=None):
    LOG.debug('create_app')

    app = Quart(__name__)  # static_folder/template_folder resolve to package dir
    if config:
        app.config.from_mapping(config)

    from .blueprints.api import api
    app.register_blueprint(api)

    # allow hash() to be used in templates
    app.jinja_env.globals.update(hash=hash)

    @app.before_serving
    async def startup():
        LOG.debug('startup') # TODO debug_call

    @app.after_serving
    async def shutdown():
        LOG.debug('shutdown') # TODO debug_call

    return app

def main():
    create_app().run()

if __name__ == '__main__':
    main()
