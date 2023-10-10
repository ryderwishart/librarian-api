import os
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI
from modal import (
    Image,
    Mount,
    Secret,
    Stub,
    Volume,
    asgi_app,
    method,
    web_endpoint,
)

web_app = FastAPI()
assets_path = Path(__file__).parent / "genesis-ai-datasets"


image = (
    Image.debian_slim(python_version="3.11")
    .pip_install(
        "lancedb",
        "poetry"
    )
    .apt_install("git", "wget")
    .run_commands(
        "mkdir data",
        "mkdir data/macula",
        "git clone https://github.com/Clear-Bible/genesis-ai-datasets.git",
        "wget https://github.com/Clear-Bible/macula-hebrew/raw/main/TSV/macula-hebrew.tsv -O data/macula/macula-hebrew.tsv",
        "wget https://github.com/Clear-Bible/macula-greek/raw/main/SBLGNT/tsv/macula-greek-SBLGNT.tsv -O data/macula/macula-greek-SBLGNT.tsv",
    )
)


stub = Stub(name="genesis", image=image)
DATA_DIR = Path("/genesis-ai-datasets")
volume = Volume.persisted("genesis-volume")
stub.volume = volume

# A persisted `modal.Volume` will store model artefacts across Modal app runs.
# This is crucial as finetuning runs are separate from the Gradio app we run as a webhook.


@stub.function()
@web_endpoint(method="GET")
def hello_world():
    return {"message": "Hello World", "data": DATA_DIR, 'files in data': os.listdir(DATA_DIR)}

# example hello world {"message":"Hello World","data":"/genesis-ai-datasets","files in data":["ccel-datasets","README.md",".git","misc-datasets","alignments"]}
@stub.function()
@web_endpoint(method="GET")
def create_lancedb_from_datasets():
    """Walks through DATA_DIR (excluding dot files) and creates a lancedb from the files it finds."""
    txt_files = []
    json_files = []
    jsonl_files = []
    tsv_files = []

     # walk through DATA_DIR
    for root, dirs, files in os.walk(DATA_DIR):
        # for each file in the directory
        for file in files:
            # filter out any dot files or hidden files
            if not file.startswith("."):
                full_path = os.path.join(root, file)
                # if the file is a .txt file
                if file.endswith(".txt"):
                    os.system(f"lancedb create {full_path}")
                    txt_files.append(full_path)
                elif file.endswith(".json"):
                    # Handle .json files
                    json_files.append(full_path)
                    # Add code here if you want to do something specific for .json files
                elif file.endswith(".jsonl"):
                    # Handle .jsonl files
                    jsonl_files.append(full_path)
                    # Add code here if you want to do something specific for .jsonl files
                elif file.endswith(".tsv"):
                    # Handle .tsv files
                    tsv_files.append(full_path)
                    # Add code here if you want to do something specific for .tsv files

    # TODO: ingest each file into data frame
    # TODO: send ben the model link Can we have a github action ? 
