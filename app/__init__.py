# Third-party imports
from flask import Flask

# Local imports
from config import config
from app.route import register_all_blueprints

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Register all blueprints
    register_all_blueprints(app)
    
    return app
