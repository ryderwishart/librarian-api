# Alignments datasets

The files in this folder are compressed for git. Please unzip to use.

E.g., on Linux (from this directory), run:

```bash
find . -name '*.zip' -exec sh -c 'unzip -d "$(dirname "$1")" "$1"' _ {} \;
```

The rename_keys.py script can be used to rename the keys in the json files to fix any ambiguous paths to make automatic schema inference work in Clickhouse, for example.
