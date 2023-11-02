# librarian-api

## Running server and client on Linux

Gather data:

`git clone https://github.com/ryderwishart/librarian-api.git`
`cd librarian-api`

Unzip all compressed datasets:

```bash
sudo apt-get update
sudo apt-get install unzip
```

Start Clickhouse server to init the database:

`curl https://clickhouse.com/ | sh`
`./clickhouse server`

Kill the server once it says "Ready for Connections".

Next, move all data files to clickhouse user_files (need to start server at least once before you do this)

```bash
cp -r ./data/* user_files/
cd user_files
find . '*.zip' -exec sh -c 'unzip -d "$(dirname "$1")" "$1"' _ {} \;
find . -name '__MACOSX' -exec rm -rf {} + 2>/dev/null
cd ..
```


If you mess up at any point you can do this 
`rm -rf user_files/*`

## Format alignment JSONL files for ClickHouse

Extract VREF from alignment files, and make it the first field in a new tsv file. This allows you to query alignment rows by VREF in clickhouse very quickly and easily, without re-modelling the alignment files before ingestion.

Let's also format the alignment files by turning escaped double quotes into single quotes (otherwise clickhouse will escape all the other double quotes, and then parsing the JSON there will be no distinction between content quotes and JSON syntax quotes):

```bash
find user_files -name '*.jsonl' -print0 | xargs -0 -I{} sed -i.bak -e 's/{"vref": "\([^"]*\)".*/\1\t&/' -e 's/\\"/'\''/g' {}
```


If needed, you can also find all keys called "alignments" and rename them to "alignment":

```bash
find user_files -name '*.jsonl' -print0 | xargs -0 -I{} sed -i.bak -e 's/"alignments"/"alignment"/g' {}
```

Remove all backup files if all went well:

```bash
find user_files -name "*.bak" -type f -delete
```

In another shell, start the client

`./clickhouse client`

Data can be queried directly from files by using the `file()` function. For example:

```sql
SELECT * FROM file('alignments/spanish/spapddpt_alignments_final_output.jsonl', 'TSV') LIMIT 1
```

## Cleaning up the HOTTP data for clickhouse

We're just turning out json data into TSV by extracting a primary key and making it field 1.

```bash
cd user_files/hottp
# The transform script should be right in the HOTTP folder
python3 make_tsv_from_hottp_json.py
cd ../..
```

## Running the flask server

### If everything is installed

```bash
# Navigate to scripts folder
cd scripts
# Create virtual env
python3 -m venv api_venv
# Activate virtual env
source api_venv/bin/activate
# Install dependencies
pip install -r requirements.txt
# Run the server
./run_server.sh 
```

While the server is running, you can access the clickhouse client using:

```bash
../../clickhouse client
```

### Setup for the first time

Install Flask, clickhouse-driver, and gunicorn:

`apt install python3-pip`

`sudo apt-get install python3-venv`

`python3 -m venv api_venv`

`source api_venv/bin/activate`

`pip install Flask clickhouse-driver gunicorn python-dotenv flask_httpauth flask_cors`

`python3 init_server.py`

`gunicorn -w 1 -b 0.0.0.0:5001 server_with_tables:app` -- Note the port number, and adjust your queries according to whatever port you use.


If you are having trouble finding the virtual env for gunicorn (or another library), try specifying the full path. E.g.,

`./api_venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 server_with_tables:app`

Using postman, test the API endpoint by querying:

`http://localhost:5001/resolveIds?ids=o010040010011`

```json
[
    {
        "maculaId": "o010040010011",
        "marbleId": "00100400100002"
    }
]
```

## Ports

If your private IP works, but your public ip doesn't, you might need to run `sudo ufw allow 5000/tcp` to allow traffic.