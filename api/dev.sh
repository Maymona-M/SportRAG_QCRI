#!/usr/bin/env bash
set -euo pipefail

# dev.sh - development entrypoint for the API container.
# It runs the Flask app using the Flask CLI on port 8000 so it matches the
# compose port mapping (host -> container 8000).

# Ensure Python can import sibling packages copied into the image (/opt/app)
export PYTHONPATH=/opt/app:${PYTHONPATH:-}

# Run the Flask app module under the /api directory. Use the module path so
# Python can import sibling packages (e.g. `scripts`).
export FLASK_APP=app.py
export FLASK_ENV=development

echo "Starting Flask dev server on 0.0.0.0:8000 (PYTHONPATH=$PYTHONPATH)"
exec flask run --host=0.0.0.0 --port=8000
