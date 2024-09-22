import gc
import psutil
import datetime
import threading

from config import logger
from .views import update_and_broadcast
from flask import abort, current_app, request, Response
from linebot.exceptions import InvalidSignatureError


def init_routes(app):
    # Line Bot Testing route
    @app.route("/callback", methods=["POST"])
    def callback():
        signature = request.headers["X-Line-Signature"]
        body = request.get_data(as_text=True)
        app.logger.info("Request body: " + body)
        try:
            handler = current_app.config["WEBHOOK_HANDLER"]
            handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)
        return "OK"

    # Default route
    @app.route("/", methods=["GET"])
    def home():
        return Response(status=200)

    # Wakeup route - for server health check and memory clean
    @app.route("/wakeup", methods=["GET"])
    def wakeup():
        gc.collect()
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024**2
        logger.info(f"目前記憶體使用量 {memory_usage:.2f} MB")
        return Response(status=200)

    # Update route - for updating and broadcasting
    @app.route("/update", methods=["GET"])
    def update():
        # Check if API-Access-Token header is provided
        if "API-Access-Token" not in request.headers:
            return Response("Missing API-Access-Token", status=401)
        # Check if the provided token is correct
        elif request.headers["API-Access-Token"] != current_app.config["API_ACCESS_TOKEN"]:
            return Response("Invalid API-Access-Token", status=401)
        else:
            logger.info("開始進行推薦")
            # Assign update and broadcast
            update_and_broadcast_thread = threading.Thread(target=update_and_broadcast)
            update_and_broadcast_thread.start()
            return Response(status=200)
        
    # Test route - for testing usage
    @app.route("/test", methods=["GET"])
    def test():
        # Check if API-Access-Token header is provided
        if "API-Access-Token" not in request.headers:
            return Response("Missing API-Access-Token", status=401)
        # Check if the provided token is correct
        elif request.headers["API-Access-Token"] != current_app.config["API_ACCESS_TOKEN"]:
            return Response("Invalid API-Access-Token", status=401)
        else:
            logger.info("開始進行測試")
            # Assign update and broadcast
            target_date_str = request.headers["Target-Date"]  # with format "YYYY-MM-DD"
            target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
            update_and_broadcast_thread = threading.Thread(target=update_and_broadcast, args=(target_date, False))
            update_and_broadcast_thread.start()
            return Response(status=200)
