import os
from app import create_app

# TODO: Update technical strategy settings
# TODO: Unit test
# TODO: Use target_date to replace now or today & test with specific date
# TODO: Server avaliability optimization

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
