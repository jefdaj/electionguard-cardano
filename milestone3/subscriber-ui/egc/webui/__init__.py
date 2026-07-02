from quart import Quart

def create_app(config=None):
    app = Quart(__name__)  # static_folder/template_folder resolve to package dir
    if config:
        app.config.from_mapping(config)

    from .blueprints.main import bp as main_bp
    from .blueprints.partials import bp as partials_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(partials_bp, url_prefix="/partials")
    return app

