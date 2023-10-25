#!/bin/bash

echo "Setting up virtual environment..."
# Activate the virtual environment
source api_venv/bin/activate

echo "Attempting to stop any running ClickHouse and Gunicorn processes..."
# Kill any running ClickHouse and Gunicorn processes
pkill -f clickhouse
pkill -f gunicorn

echo "Starting ClickHouse server..."
# Start ClickHouse server in the background, redirecting output to /dev/null
nohup ../../clickhouse server >/dev/null 2>&1 &

# Wait for ClickHouse server to start
echo "Waiting for ClickHouse server to start..."
while ! curl --output /dev/null --silent --head --fail http://localhost:8123; do sleep 1 && echo -n .; done
echo "ClickHouse server started."

echo "Starting WSGI server..."
# Start the Flask application with Gunicorn in the background, redirecting output to /dev/null
nohup gunicorn -w 4 -b 0.0.0.0:5000 server_with_tables:app >/dev/null 2>&1 &
# Wait for the WSGI server to start
# echo "Waiting for WSGI server to start..."
# while ! curl --output /dev/null --silent --head --fail 'http://localhost:5000/query?file=macula/macula-with-marble-ids.tsv&search_string=ROM 1:9&column_name=VREF&limit=3'; do sleep 1 && echo -n .; done
sleep 3
echo "API server started on port 5000."
# Optionally, you can redirect output to log files instead of /dev/null for debugging purposes:
# nohup ./clickhouse server > clickhouse.log 2>&1 &
# nohup gunicorn -w 4 -b 0.0.0.0:5000 server_with_tables:app > gunicorn.log 2>&1 &
