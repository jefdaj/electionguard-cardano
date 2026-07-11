import uvicorn
from egc_app.server.app import create_app

def run(dev_mode: bool, **cfg_kwargs):
    if dev_mode:
        uvicorn.run(
            "egc_app.server.app:create_app",
            factory=True,
            reload=True,
            workers=1,
            log_level="debug",
            **cfg_kwargs # TODO any cfg args not accepted here?
        )
    else:
        # production
        # TODO what else should be set here?
        app = create_app()
        cfg = uvicorn.Config(app, **cfg_kwargs)
        server = uvicorn.Server(cfg)
        server.run()

if __name__ == "__main__":
    run()
