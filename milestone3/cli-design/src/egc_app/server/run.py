import uvicorn
from egc_app.server.app import create_app

def main():
    app = create_app()
    cfg = uvicorn.Config(app, host="0.0.0.0", port=8000, reload=True)
    server = uvicorn.Server(cfg)
    server.run()

if __name__ == "__main__":
    main()
