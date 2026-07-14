from contextlib import asynccontextmanager
from fastapi import FastAPI
from egc_app.server.routers.api.router import router as api_router
from egc_app.server.routers.web.router import router as web_router
from egc_app.server.state import setup_state, teardown_state
from fastapi.staticfiles import StaticFiles
from pathlib import Path

import logging
LOG = logging.getLogger(__name__)

STATIC_DIR = str(
    Path(__file__).resolve().parent / 'static'
)

# TODO AppConfig type?
def create_app(config: dict) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # startup: init lib resources, DB pools, etc.
        setup_state(app.state, config)
        yield
        # shutdown: cleanup
        teardown_state(app.state)

    app = FastAPI(lifespan=lifespan)
    app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')
    app.include_router(api_router)
    app.include_router(web_router)
    return app
