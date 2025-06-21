# # Third-party imports
# from flask import Blueprint, Response, current_app, request


# # Create the blueprint
# bp = Blueprint("strategy", __name__, url_prefix="/strategy")


# # Route to get available rule types
# @bp.route("/rule-types", methods=["GET"])
# def get_rule_types():
#     """
#     Get a list of available rule types.
    
#     Responses:
#     - 200 OK: Returns a list of rule type names
#     """
#     return Response(current_app.rule_factory.get_available_rule_types(), status=200)

# # Route to create a new strategy
# @bp.route("/user/<user_id>/strategies", methods=["POST"])
# def create_strategy(user_id):
#     """
#     Create a new strategy for a user.
    
#     Path Parameters:
#     - user_id: The ID of the user
    
#     Request Body:
#     - name: The name of the strategy
#     - description: A description of the strategy
#     - rules: A list of rule dictionaries
    
#     Responses:
#     - 201 Created: Returns the created strategy
#     - 400 Bad Request: If the request body is invalid
#     - 409 Conflict: If a strategy with the same name already exists
#     """
#     data = request.json
    
#     # Validate request body
#     if not data:
#         return Response({"error": "Missing request body"}, status=400)
    
#     name = data.get("name")
#     if not name:
#         return Response({"error": "Missing strategy name"}, status=400)
    
#     try:
#         strategy = current_app.strategy_service.create_strategy(
#             user_id=user_id,
#             name=name,
#             description=data.get("description", ""),
#             rules=data.get("rules", [])
#         )
#         return Response(strategy.to_dict(), status=201)
#     except ValueError as e:
#         return Response({"error": str(e)}, status=409)

# # Route to get all strategies for a user
# @bp.route("/user/<user_id>/strategies", methods=["GET"])
# def get_user_strategies(user_id):
#     """
#     Get all strategies for a user.
    
#     Path Parameters:
#     - user_id: The ID of the user
    
#     Responses:
#     - 200 OK: Returns a list of strategies
#     """
#     strategies = current_app.strategy_service.get_user_strategies(user_id)
#     return Response([strategy.to_dict() for strategy in strategies], status=200)

# # Route to get a specific strategy
# @bp.route("/user/<user_id>/strategies/<strategy_name>", methods=["GET"])
# def get_strategy(user_id, strategy_name):
#     """
#     Get a specific strategy.
    
#     Path Parameters:
#     - user_id: The ID of the user
#     - strategy_name: The name of the strategy
    
#     Responses:
#     - 200 OK: Returns the strategy
#     - 404 Not Found: If the strategy doesn't exist
#     """
#     strategy = current_app.strategy_service.get_strategy(user_id, strategy_name)
#     if not strategy:
#         return Response({"error": "Strategy not found"}, status=404)
    
#     return Response(strategy.to_dict(), status=200)

# # Route to update a strategy
# @bp.route("/user/<user_id>/strategies/<strategy_name>", methods=["PUT"])
# def update_strategy(user_id, strategy_name):
#     """
#     Update a strategy.
    
#     Path Parameters:
#     - user_id: The ID of the user
#     - strategy_name: The name of the strategy
    
#     Request Body:
#     - description: A new description of the strategy (optional)
#     - rules: A new list of rule dictionaries (optional)
    
#     Responses:
#     - 200 OK: Returns the updated strategy
#     - 404 Not Found: If the strategy doesn't exist
#     """
#     data = request.json
    
#     # Validate request body
#     if not data:
#         return Response({"error": "Missing request body"}, status=400)
    
#     strategy = current_app.strategy_service.update_strategy(
#         user_id=user_id,
#         strategy_name=strategy_name,
#         description=data.get("description"),
#         rules=data.get("rules")
#     )
    
#     if not strategy:
#         return Response({"error": "Strategy not found"}, status=404)
    
#     return Response(strategy.to_dict(), status=200)

# # Route to delete a strategy
# @bp.route("/user/<user_id>/strategies/<strategy_name>", methods=["DELETE"])
# def delete_strategy(user_id, strategy_name):
#     """
#     Delete a strategy.
    
#     Path Parameters:
#     - user_id: The ID of the user
#     - strategy_name: The name of the strategy
    
#     Responses:
#     - 204 No Content: If the strategy was deleted
#     - 404 Not Found: If the strategy doesn't exist
#     """
#     success = current_app.strategy_service.delete_strategy(user_id, strategy_name)
#     if not success:
#         return Response({"error": "Strategy not found"}, status=404)
    
#     return "", 204

# # # Route to execute a strategy on stock data (optionally save the result)
# # @bp.route("/execute", methods=["POST"])
# # def execute_strategy():
# #     """
# #     Execute a strategy on stock data.
    
# #     Request Body:
# #     - strategy: A strategy dictionary
# #     - stock_data: Stock data to apply the strategy to
    
# #     Responses:
# #     - 200 OK: Returns the filtered stock data
# #     - 400 Bad Request: If the request body is invalid
# #     """
# #     data = request.json
    
# #     # Validate request body
# #     if not data:
# #         return Response({"error": "Missing request body"}, status=400)
    
# #     strategy_dict = data.get("strategy")
# #     if not strategy_dict:
# #         return Response({"error": "Missing strategy"}, status=400)
    
# #     stock_data = data.get("stock_data")
# #     if not stock_data:
# #         return Response({"error": "Missing stock data"}, status=400)
    
# #     # Convert stock data to DataFrame
# #     import pandas as pd
# #     df = pd.DataFrame(stock_data)
    
# #     # Create a temporary strategy
# #     from app.strategy.common.user_strategy import UserStrategy
# #     strategy = UserStrategy.from_dict(strategy_dict, current_app.rule_factory)
    
# #     # Apply the strategy
# #     result = strategy.apply(df)
    
# #     # Return the filtered stock data
# #     filtered_data = df[result].to_dict(orient="records")
# #     return Response(filtered_data, status=200)
