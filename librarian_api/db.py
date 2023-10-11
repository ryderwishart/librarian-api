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
        "poetry",
        "pandas"
    )
    .apt_install("git", "wget")
    .run_commands(
        "mkdir data",
        "cd data",
        "mkdir macula",
        "git clone https://github.com/Clear-Bible/genesis-ai-datasets.git",
        "wget https://github.com/Clear-Bible/macula-hebrew/raw/main/TSV/macula-hebrew.tsv",
        "wget https://github.com/Clear-Bible/macula-greek/raw/main/SBLGNT/tsv/macula-greek-SBLGNT.tsv",
        "mv macula-hebrew.tsv macula/macula-hebrew.tsv",
        "mv macula-greek-SBLGNT.tsv macula/macula-greek-SBLGNT.tsv",
        "cd .."
    )
)
import os
# os.chdir("librarian_api")
print('current dir', os.listdir(Path.cwd()))


stub = Stub(name="genesis", image=image)
DATA_DIR = Path("./data")
print('data:', DATA_DIR, os.listdir(DATA_DIR))
volume = Volume.persisted("genesis-volume")
stub.volume = volume

import pandas as pd
import lancedb
import os, json


"""Walks through DATA_DIR (excluding dot files) and creates a lancedb from the files it finds."""
macula_files = [file for file in os.listdir(DATA_DIR / 'macula') if file.endswith('.tsv')]
txt_files = [] # e.g., /genesis-ai-datasets/ccel-datasets/modified/Adeney.Walter.Expositors.Ezra.Nehimiah.Esther.commentary.txt
alignment_files = [] # e.g., /genesis-ai-datasets/alignments/french/addressed_chunks/data-chunk-aa.jsonl

# populate txt and alignment files
# FIXME: gather alignment files in a more robust manner
for root, dirs, files in os.walk(DATA_DIR):
    for file in files:
        if file.endswith(".txt"):
            txt_files.append(os.path.join(root, file))
        elif file.endswith(".jsonl") and "alignments" in root and "addressed_chunks" in root:
            alignment_files.append(os.path.join(root, file))



# Creating pandas DataFrames for each type of file
print(f'Building Text DataFrame from {len(txt_files)} files...')
text_df = pd.DataFrame()

for path in txt_files:
    with open(path, 'r', encoding='utf8') as f:
        print(f'Adding {path} to text_df...')
        try:
            text_df = pd.concat([text_df, pd.DataFrame([f.read()], columns=['text'])])
        except UnicodeDecodeError:
            print(f'UnicodeDecodeError: {path}')

print(f'Building Alignments DataFrame from {len(alignment_files)} files...')
alignment_df = pd.DataFrame()

for path in alignment_files:
    with open(path, 'r', encoding='utf8') as f:
        print(f'Adding {path} to alignment_df...')
        try:
            data = [json.loads(line) for line in f]
            normalized_data = pd.json_normalize(data, sep='_')
            alignment_df = pd.concat([alignment_df, normalized_data])
        except UnicodeDecodeError:
            print(f'UnicodeDecodeError: {path}')


print(f'Building MACULA DataFrame from {len(macula_files)} files...')
macula_df = pd.DataFrame()

for path in macula_files:
    with open(DATA_DIR / 'macula' / path, 'r', encoding='utf8') as f:
        print(f'Adding {path} to macula_df...')
        # Note, these are TSV files
        try:
            macula_df = pd.concat([macula_df, pd.read_csv(f, sep='\t')])
        except UnicodeDecodeError:
            print(f'UnicodeDecodeError: {path}')
        

# Print some info about the DataFrames/columns
print('text_df info:', text_df.info())
print('alignment_df info:', alignment_df.info())
print('macula_df info:', macula_df.info())

# Create an embedding function
from sentence_transformers import SentenceTransformer

name="paraphrase-albert-small-v2"
model = SentenceTransformer(name)

# used for both training and querying
def embed_batch(batch):
    print(f'Embedding batch of size {len(batch)}')
    try:
        return [model.encode(sentence) for sentence in batch]
    except Exception as e:
        print('Error:', e)
        return []

# The following two lines will embed your text columns

# text_df['vector'] = text_df['text'].apply(embed_batch)
# alignment_df['vector'] = alignment_df['text'].apply(embed_batch)

# stringify the alignments data as it is structured, and this is not compatible with lancedb
alignment_df['alignment'] = alignment_df['alignment'].apply(json.dumps)

# stringify the macula_token_ids data as it is structured, and this is not compatible with lancedb
alignment_df['macula_token_ids'] = alignment_df['macula_token_ids'].apply(json.dumps)

db = lancedb.connect("./lancedb")
print('Creating TXT table...')
text_table = db.create_table("texts", text_df, mode='overwrite')
print('Creating Alignments table...')
alignment_tables = db.create_table("alignments", alignment_df, mode='overwrite')

@stub.function()
@web_endpoint(method="GET")
def hello_world():
    return {"message": "Hello World", "macula data": os.listdir(DATA_DIR), 'genesis data': os.listdir(DATA_DIR), 'dfs and columns': {'text_df': text_df.columns, 'alignment_df': alignment_df.columns, 'macula_df': macula_df.columns}}
