# Third-party imports
from flask import Flask

# Local imports
from config import config
from .routes import init_routes
from app.strategy.core.controller import create_rule_factory, create_strategy_blueprint

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize the app with the routes
    init_routes(app)
    
    # Create a rule factory
    rule_factory = create_rule_factory()
    
    # Create and register the strategy blueprint
    with app.app_context():
        strategy_bp = create_strategy_blueprint(rule_factory)
        app.register_blueprint(strategy_bp)
    
    return app
