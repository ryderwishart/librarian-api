#!/bin/bash

# Activate the virtual environment
source api_venv/bin/activate

# Start ClickHouse server in the background, redirecting output to /dev/null
nohup ./clickhouse server >/dev/null 2>&1 &

# Start the Flask application with Gunicorn in the background, redirecting output to /dev/null
nohup gunicorn -w 4 -b 0.0.0.0:5000 server_with_tables:app >/dev/null 2>&1 &

# Optionally, you can redirect output to log files instead of /dev/null for debugging purposes:
# nohup ./clickhouse server > clickhouse.log 2>&1 &
# nohup gunicorn -w 4 -b 0.0.0.0:5000 server_with_tables:app > gunicorn.log 2>&1 &
