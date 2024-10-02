import gc
import psutil
import datetime
import threading

from config import logger
from .views import update_and_broadcast
from flask import current_app, request, Response
from linebot.exceptions import InvalidSignatureError


def init_routes(app):
    
    @app.route("/", methods=["GET"])
    def home():
        """
        Default route for the application.

        Responses:
        - 200 OK: Indicates the server is up and running.
        """
        return Response(status=200)
    
    
    @app.route("/callback", methods=["POST"])
    def callback():
        """
        Handle incoming webhook events from LINE Bot.

        Headers:
        - `X-Line-Signature`: Signature for request verification.

        Responses:
        - 200 OK: If the request is successfully processed.
        - 400 Bad Request: If `X-Line-Signature` is missing or invalid.
        """
        # Extracting signature and body from request
        signature = request.headers.get("X-Line-Signature")
        body = request.get_data(as_text=True)
        app.logger.info(f"Request body: {body}")
        try:
            handler = current_app.config["WEBHOOK_HANDLER"]
            handler.handle(body, signature)
        except InvalidSignatureError:
            return Response("Invalid signature", status=400)
        return Response(status=200)


    @app.route("/wakeup", methods=["GET"])
    def wakeup():
        """
        Wake up the service and check memory usage.

        Responses:
        - 200 OK: If the request is successfully processed.
        """
        gc.collect()
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024**2
        logger.info(f"目前記憶體使用量 {memory_usage:.2f} MB")
        return Response(status=200)


    @app.route("/update", methods=["GET"])
    def update():
        """
        Update data and optionally broadcast stock recommendations.

        Headers:
        - `API-Access-Token` (required): A token to authorize access to this API.
        - `Target-Date` (optional): The date for retrieving data and generating stock recommendations, in "YYYY-MM-DD" format.
        - `Need-Broadcast` (optional): A flag to determine whether the stock recommendation should be broadcasted via Line Bot.
            - Accepts values "true" or "false" (case-insensitive). Defaults to "false" if not provided.

        Responses:
        - 200 OK: If the request is successfully processed.
        - 400 Bad Request: If `Target-Date` has an invalid format.
        - 401 Unauthorized: If `API-Access-Token` is missing or invalid.
        """
        # Check if API-Access-Token header is provided
        if "API-Access-Token" not in request.headers:
            return Response("Missing API-Access-Token", status=401)
        # Check if the provided token is correct
        elif request.headers["API-Access-Token"] != current_app.config["API_ACCESS_TOKEN"]:
            return Response("Invalid API-Access-Token", status=401)
        else:
            target_date = request.headers.get("Target-Date", None)  # with format "YYYY-MM-DD"
            
            if target_date:
                try:
                    target_date = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
                except ValueError:
                    return Response("Invalid Target-Date format", status=400)
                
            need_broadcast = request.headers.get("Need-Broadcast", "false").lower() == "true"
            logger.info("開始進行推薦")
            # Assign update and broadcast
            app = current_app._get_current_object()
            update_and_broadcast_thread = threading.Thread(target=update_and_broadcast, args=(app, target_date, need_broadcast))
            update_and_broadcast_thread.start()
            return Response(status=200)
