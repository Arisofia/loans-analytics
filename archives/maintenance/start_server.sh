#!/bin/bash
source .venv/bin/activate
nohup uvicorn python.apps.analytics.api.main:app --host 0.0.0.0 --port 8000 --reload >uvicorn.log 2>&1 &
echo $! >uvicorn.pid
