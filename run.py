"""
Application Entry Point
Run this file to start the Flask development server.

Usage:
    python run.py

For production, use Gunicorn instead:
    gunicorn -w 3 -b 127.0.0.1:8000 "run:app"
"""

import os
from app import create_app

# Create the application instance.
# Config is auto-detected from FLASK_ENV via get_config() in config.py.
app = create_app()

if __name__ == "__main__":
    host = os.environ.get("APP_HOST", "0.0.0.0")
    port = int(os.environ.get("APP_PORT", 5000))
    debug = app.config.get("DEBUG", False)

    print(f"\n{'='*50}")
    print(f"  🚀 InventoryPro starting up!")
    print(f"  📍 URL: http://{host}:{port}")
    print(f"  🔧 Debug mode: {'ON' if debug else 'OFF'}")
    print(f"{'='*50}\n")

    app.run(host=host, port=port, debug=debug)