from contextlib import asynccontextmanager
from fastapi import FastAPI
from egc_app.server.routers.api.router import router as api_router
from egc_app.server.routers.web.router import router as web_router

# just to check that it works for now:
from egc import *

import logging
LOG = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: init lib resources, DB pools, etc.
    app.state.trivial = 0 # TODO remove trivial_state
    app.state.subscriber = None
    app.state.subscriber.start()
    yield
    # shutdown: cleanup
    app.state.subscriber.stop()

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(api_router)
    app.include_router(web_router)
    return app

# old code for reference:
# from quart import Quart, Config
# def create_app(config=None):
#     LOG.debug('create_app')
#     app = Quart(__name__)  # static_folder/template_folder resolve to package dir
#     # for testing the api
#     app.state = 0
#     app.subscriber = None
#     if config:
#         app.config.from_mapping(config)
#     from .blueprints.api import api
#     app.register_blueprint(api)
#     # allow hash() to be used in templates
#     app.jinja_env.globals.update(hash=hash)
#     @app.before_serving
#     async def startup():
#         LOG.debug('startup') # TODO debug_call
#     @app.after_serving
#     async def shutdown():
#         LOG.debug('shutdown') # TODO debug_call
#     return app
