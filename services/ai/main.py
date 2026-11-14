# Entrypoint: run with python services/ai/main.py from the repo root.
# Serves the AI assistant on port 8001.

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

from app import create_app

app = create_app()

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)
