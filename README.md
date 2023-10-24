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

`find . -name '*.zip' -exec sh -c 'unzip -d "$(dirname "$1")" "$1"' _ {} \;`
`find . -name '__MACOSX' -exec rm -rf {} + 2>/dev/null`

Move all files to clickhouse user_files (might need to start server at least once before you do this?)

`mv ./data/* ../user_files/`

Start Clickhouse server and client

`curl https://clickhouse.com/ | sh`
`./clickhouse server`

In another shell, start the client

`./clickhouse client`

## Data structure (Oct 23, 2023)

```bash
user_files/
├── alignments
│   ├── README.md
│   ├── french
│   │   ├── complete_bible_fraLSG_final_output_updated.jsonl
│   │   └── complete_bible_fraLSG_final_output_updated.jsonl.zip
│   ├── rename_keys.py
│   ├── spanish
│   │   ├── spapddpt_alignments_final_output_updated.jsonl
│   │   └── spapddpt_alignments_final_output_updated.jsonl.zip
│   └── tok_pisin
│       ├── alignments_tpiOTNT-pseudo_english_gpt-3.5-turbo-instruct_20230927_final_output_updated.jsonl
│       └── alignments_tpiOTNT-pseudo_english_gpt-3.5-turbo-instruct_20230927_final_output_updated.jsonl.zip
├── hottp
│   ├── HOTTP_translated_por_Latn.json
│   ├── HOTTP_translated_por_Latn.json.zip
│   ├── HOTTP_translated_spa_Latn.json
│   └── HOTTP_translated_spa_Latn.json.zip
├── images
│   ├── UBS-images-metadata.tsv_updated.tsv
│   └── UBS-images-metadata.tsv_updated.tsv.zip
└── macula
    ├── macula-with-marble-ids.tsv
    └── macula-with-marble-ids.tsv.zip  [NOTE: this file currently has a double header to force ClickHouse to read all columns as strings]
```

Data can be queried directly from files by using the `file()` function. For example:

```sql
SELECT * FROM file('user_files/alignments/spanish/spapddpt_alignments_final_output_updated.jsonl')
```


## Running the flask server

Install Flask, clickhouse-driver, and gunicorn:

`apt install python3-pip`

`sudo apt-get install python3-venv`

`python3 -m venv api_venv`

`source api_venv/bin/activate`

`pip install Flask clickhouse-driver`

`pip install gunicorn`

`gunicorn -w 4 -b 0.0.0.0:5000 server:app` or 
`gunicorn -w 4 -b 0.0.0.0:5000 server_with_tables:app`

Using postman, test the API endpoint by querying:

`http://{DROPLET_IP_ADDRESS}:5000/query`

```json
{
    "file": "macula/macula-with-marble-ids.tsv"
}
```

Examples:
`http://{DROPLET_IP_ADDRESS}:5000/query?file=macula/macula-with-marble-ids.tsv&search_string=ROM 1:9&column_name=VREF&limit=3`
`http://{DROPLET_IP_ADDRESS}:5000/alignments?vref=ROM 5:6&limit=5`

## Format alignment JSONL files for ClickHouse

```bash
find . -name '*.jsonl' -print0 | xargs -0 -I{} sed -i.bak -e 's/{"vref": "\([^"]*\)".*/\1\t&/' {}
```

With limited file space you can skip the backup file (since you can always restore from the original zip file):

```bash
find . -name '*.jsonl' -print0 | xargs -0 -I{} sed -i -e 's/{"vref": "\([^"]*\)".*/\1\t&/' {}
```
