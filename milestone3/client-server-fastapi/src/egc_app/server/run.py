import uvicorn
from egc_app.server.app import create_app

app = create_app()

def main():
    uvicorn.run("egc_app.server.run:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
