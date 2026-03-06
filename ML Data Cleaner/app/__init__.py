import os
from flask import Flask

# Project root is one level above this file (app/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["UPLOAD_FOLDER"] = os.path.join(_PROJECT_ROOT, "uploads")
    app.config["OUTPUT_FOLDER"] = os.path.join(_PROJECT_ROOT, "outputs")
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB

    from .routes import bp
    app.register_blueprint(bp)

    return app
