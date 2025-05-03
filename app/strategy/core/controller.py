# Standard library imports
import os

# Third-party imports
from flask import Blueprint, request, jsonify, current_app

# Local imports
from app.rule.common.factory import RuleFactory
from app.strategy.core.service import StrategyService

# Import rule classes
from app.rule.core.technical import *
from app.rule.core.fundamental import *
from app.rule.core.chip import *


def create_strategy_blueprint(rule_factory: RuleFactory = None) -> Blueprint:
    """
    Create a Flask Blueprint for strategy-related endpoints.
    
    Args:
        rule_factory: A RuleFactory instance, or None to create a new one
        
    Returns:
        A Flask Blueprint
    """
    if rule_factory is None:
        rule_factory = create_rule_factory()
    
    # Create a storage directory
    storage_dir = os.path.join(current_app.instance_path, "strategies")
    os.makedirs(storage_dir, exist_ok=True)
    
    # Create the strategy service
    strategy_service = StrategyService(storage_dir, rule_factory)
    
    # Create the blueprint
    strategy_bp = Blueprint("strategy", __name__, url_prefix="/strategy")
    
    # Register the strategy service with the app
    current_app.strategy_service = strategy_service
    
    # Route to get available rule types
    @strategy_bp.route("/rule-types", methods=["GET"])
    def get_rule_types():
        """
        Get a list of available rule types.
        
        Responses:
        - 200 OK: Returns a list of rule type names
        """
        return jsonify(rule_factory.get_available_rule_types())
    
    # Route to create a new strategy
    @strategy_bp.route("/user/<user_id>/strategies", methods=["POST"])
    def create_strategy(user_id):
        """
        Create a new strategy for a user.
        
        Path Parameters:
        - user_id: The ID of the user
        
        Request Body:
        - name: The name of the strategy
        - description: A description of the strategy
        - rules: A list of rule dictionaries
        
        Responses:
        - 201 Created: Returns the created strategy
        - 400 Bad Request: If the request body is invalid
        - 409 Conflict: If a strategy with the same name already exists
        """
        data = request.json
        
        # Validate request body
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        
        name = data.get("name")
        if not name:
            return jsonify({"error": "Missing strategy name"}), 400
        
        try:
            strategy = strategy_service.create_strategy(
                user_id=user_id,
                name=name,
                description=data.get("description", ""),
                rules=data.get("rules", [])
            )
            return jsonify(strategy.to_dict()), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 409
    
    # Route to get all strategies for a user
    @strategy_bp.route("/user/<user_id>/strategies", methods=["GET"])
    def get_user_strategies(user_id):
        """
        Get all strategies for a user.
        
        Path Parameters:
        - user_id: The ID of the user
        
        Responses:
        - 200 OK: Returns a list of strategies
        """
        strategies = strategy_service.get_user_strategies(user_id)
        return jsonify([strategy.to_dict() for strategy in strategies])
    
    # Route to get a specific strategy
    @strategy_bp.route("/user/<user_id>/strategies/<strategy_name>", methods=["GET"])
    def get_strategy(user_id, strategy_name):
        """
        Get a specific strategy.
        
        Path Parameters:
        - user_id: The ID of the user
        - strategy_name: The name of the strategy
        
        Responses:
        - 200 OK: Returns the strategy
        - 404 Not Found: If the strategy doesn't exist
        """
        strategy = strategy_service.get_strategy(user_id, strategy_name)
        if not strategy:
            return jsonify({"error": "Strategy not found"}), 404
        
        return jsonify(strategy.to_dict())
    
    # Route to update a strategy
    @strategy_bp.route("/user/<user_id>/strategies/<strategy_name>", methods=["PUT"])
    def update_strategy(user_id, strategy_name):
        """
        Update a strategy.
        
        Path Parameters:
        - user_id: The ID of the user
        - strategy_name: The name of the strategy
        
        Request Body:
        - description: A new description of the strategy (optional)
        - rules: A new list of rule dictionaries (optional)
        
        Responses:
        - 200 OK: Returns the updated strategy
        - 404 Not Found: If the strategy doesn't exist
        """
        data = request.json
        
        # Validate request body
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        
        strategy = strategy_service.update_strategy(
            user_id=user_id,
            strategy_name=strategy_name,
            description=data.get("description"),
            rules=data.get("rules")
        )
        
        if not strategy:
            return jsonify({"error": "Strategy not found"}), 404
        
        return jsonify(strategy.to_dict())
    
    # Route to delete a strategy
    @strategy_bp.route("/user/<user_id>/strategies/<strategy_name>", methods=["DELETE"])
    def delete_strategy(user_id, strategy_name):
        """
        Delete a strategy.
        
        Path Parameters:
        - user_id: The ID of the user
        - strategy_name: The name of the strategy
        
        Responses:
        - 204 No Content: If the strategy was deleted
        - 404 Not Found: If the strategy doesn't exist
        """
        success = strategy_service.delete_strategy(user_id, strategy_name)
        if not success:
            return jsonify({"error": "Strategy not found"}), 404
        
        return "", 204
    
    # Route to execute a strategy on stock data (optionally save the result)
    @strategy_bp.route("/execute", methods=["POST"])
    def execute_strategy():
        """
        Execute a strategy on stock data.
        
        Request Body:
        - strategy: A strategy dictionary
        - stock_data: Stock data to apply the strategy to
        
        Responses:
        - 200 OK: Returns the filtered stock data
        - 400 Bad Request: If the request body is invalid
        """
        data = request.json
        
        # Validate request body
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        
        strategy_dict = data.get("strategy")
        if not strategy_dict:
            return jsonify({"error": "Missing strategy"}), 400
        
        stock_data = data.get("stock_data")
        if not stock_data:
            return jsonify({"error": "Missing stock data"}), 400
        
        # Convert stock data to DataFrame
        import pandas as pd
        df = pd.DataFrame(stock_data)
        
        # Create a temporary strategy
        from app.strategy.common.user_strategy import UserStrategy
        strategy = UserStrategy.from_dict(strategy_dict, rule_factory)
        
        # Apply the strategy
        result = strategy.apply(df)
        
        # Return the filtered stock data
        filtered_data = df[result].to_dict(orient="records")
        return jsonify(filtered_data)
    
    return strategy_bp


def create_rule_factory() -> RuleFactory:
    """
    Create and initialize a RuleFactory with all available rule types.
    
    Returns:
        An initialized RuleFactory
    """
    factory = RuleFactory()
    
    # Register all rule types
    rule_mapping = {
        # Fundamental rules
        "PERangeRule": PERangeRule,
        "PBRangeRule": PBRangeRule,
        "DividendYieldRangeRule": DividendYieldRangeRule,
        
        # Technical rules
        "SMARule": SMARule,
        "CrossAboveRule": CrossAboveRule,
        "CrossBelowRule": CrossBelowRule,
        "RSIRule": RSIRule,
        "MACDRule": MACDRule,
        "BollingerBandsRule": BollingerBandsRule,
        "VolumeRule": VolumeRule,
        
        # Chip rules
        "ForeignInvestorsRule": ForeignInvestorsRule,
        "InvestmentTrustRule": InvestmentTrustRule,
        "DealersRule": DealersRule,
        "MarginTradingRule": MarginTradingRule,
        "ShortSellingRule": ShortSellingRule,
    }
    
    factory.register_rule_types(rule_mapping)
    
    return factory 