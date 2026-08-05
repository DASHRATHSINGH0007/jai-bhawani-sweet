from flask import Flask

from config import Config
from extensions import db
from routes.api import api_bp
from routes.web import init_database, register_web_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    register_web_routes(app)
    app.register_blueprint(api_bp)

    init_database(app)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
