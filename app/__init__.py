# Standard library imports
import os

# Third-party imports
from flask import Flask

# Local imports
from app.core import config
from app.route import register_all_blueprints
from app.rule import create_rule_factory
from app.strategy import StrategyService

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    
    with app.app_context():
        # Create the rule factory
        rule_factory = create_rule_factory()
        app.rule_factory = rule_factory
        
        # Create the storage directory for strategies
        storage_dir = os.path.join(app.instance_path, "strategies")
        os.makedirs(storage_dir, exist_ok=True)
        
        # Create the strategy service
        strategy_service = StrategyService(storage_dir, rule_factory)
        app.strategy_service = strategy_service
    
    # Register all blueprints
    register_all_blueprints(app)
    
    return app
