# Third-party imports
from flask import Flask

# Local imports
from config import config
from .routes import init_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    init_routes(app)
    return app
