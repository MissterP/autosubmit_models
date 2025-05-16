#!/bin/bash
source /opt/venv/bin/activate

cd /code
RUN_PORT=${PORT:-8002}
RUN_HOST=${HOST:-0.0.0.0}

python -m src.main --mode api