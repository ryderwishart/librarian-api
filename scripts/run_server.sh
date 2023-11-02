#!/bin/bash

# Should be run from librarian-api/scripts/

echo -e "\e[32mSetting up virtual environment...\e[0m"
# Activate the virtual environment
source api_venv/bin/activate # Note, this doesn't seem to be working, so I have to do it manually before running this script

echo -e "\e[32mAttempting to stop any running ClickHouse and Gunicorn processes...\e[0m"
# Kill any running ClickHouse and Gunicorn processes
pkill -f clickhouse
pkill -f gunicorn

echo -e "\e[32mStarting ClickHouse server...\e[0m"
# Start ClickHouse server in the background, redirecting output to /dev/null
cd ..
nohup ./clickhouse server >/dev/null 2>&1 &

# Wait for ClickHouse server to start
echo -e "\e[32mWaiting for ClickHouse server to start...\e[0m"
while ! curl --output /dev/null --silent --head --fail http://localhost:8123; do sleep 1 && echo -n .; done
echo -e "\e[32mClickHouse server started.\e[0m"

cd scripts

# Run init_server.py to create the database and tables
echo -e "\e[32mCreating database and tables...\e[0m"
python3 init_server.py

echo -e "\e[32mStarting WSGI server...\e[0m"
# Start the Flask application with Gunicorn in the background, redirecting output to /dev/null
nohup gunicorn -w 4 -b 0.0.0.0:5000 server_with_tables:app >/dev/null 2>&1 &
# Wait for the WSGI server to start
# echo "Waiting for WSGI server to start..."
# while ! curl --output /dev/null --silent --head --fail 'http://localhost:5000/query?file=macula/macula.tsv&search_string=ROM 1:9&column_name=VREF&limit=3'; do sleep 1 && echo -n .; done
sleep 3
echo -e "\e[32mAPI server started on port 5000.\e[0m"
# Optionally, you can redirect output to log files instead of /dev/null for debugging purposes:
# nohup ./clickhouse server > clickhouse.log 2>&1 &
# nohup gunicorn -w 4 -b 0.0.0.0:5000 server_with_tables:app > gunicorn.log 2>&1 &
