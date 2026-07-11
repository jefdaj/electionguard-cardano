import uvicorn
from egc_app.server.app import create_app
from copy import deepcopy

def run(dev_mode: bool, **uvicorn_kwargs):
    # uvicorn's reload=True seems more trouble than it's worth...
    # if dev_mode:
        # uvicorn.run(
        #     "egc_app.server.app:create_app",
        #     factory=True,
        #     reload=True,
        #     workers=1,
        #     log_level="debug",
        # )
    # else:
    app_cfg = {}
    node_cfg = deepcopy(uvicorn_kwargs)
    node_cfg['dev_mode'] = dev_mode
    app_cfg['node'] = node_cfg
    app = create_app(app_cfg)
    cfg = uvicorn.Config(app, **uvicorn_kwargs)
    server = uvicorn.Server(cfg)
    server.run()

if __name__ == "__main__":
    run()
