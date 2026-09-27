"""Entry point: python3 run.py  ->  http://localhost:5000

Reads .env via backend/config.py, then starts the Flask app
(which itself starts the serial listener + camera worker).
"""
from backend.app import create_app
from backend.config import FLASK_PORT

if __name__ == "__main__":
    print(f"Smart RTO dashboard: http://localhost:{FLASK_PORT}")
    create_app().run(host="0.0.0.0", port=FLASK_PORT)
