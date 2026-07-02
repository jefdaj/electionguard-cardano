from quart import Quart, Config


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

    # from .blueprints.main import bp as main_bp
    # app.register_blueprint(main_bp)

    from .blueprints.partials import bp as partials_bp
    app.register_blueprint(partials_bp, url_prefix="/partials")

    @app.get("/")
    async def index():
        return await render_template("index.html")

    return app

