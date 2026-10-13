import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import create_app
from backend.config import Config, ProductionConfig

env = os.environ.get("FLASK_ENV", "development").lower()
cfg = ProductionConfig if env == "production" else Config

app = create_app(config_class=cfg, seed_demo=True)

if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = env != "production" and os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
