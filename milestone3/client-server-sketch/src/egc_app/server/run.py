from egc_app.server.app import create_app

def main():
    create_app().run(host="0.0.0.0", port=5000)

if __name__ == '__main__':
    main()
