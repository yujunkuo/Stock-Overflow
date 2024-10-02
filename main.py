import os
from app import create_app

# TODO: Unit test
# TODO: Server availability optimization
# TODO: Update technical strategy settings
# TODO: Use target_date to replace today & test with specific date (skyrocket)

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
