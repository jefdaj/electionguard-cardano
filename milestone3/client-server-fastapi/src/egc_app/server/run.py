import uvicorn
from egc_app.server.app import create_app

app = create_app()

def main():
    # TODO is 8000 standard for production and 5000 for dev?
    uvicorn.run("egc_app.server.run:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()

# old code for reference:
# from egc_app.server.app import create_app
# def run_server():
#     create_app().run(host="0.0.0.0", port=5000)
# if __name__ == '__main__':
#     run_server()
