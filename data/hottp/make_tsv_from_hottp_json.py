import json
import os

def process_json_file(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    filename = json_file.split('.')[0]

    output_file = f'{filename}.tsv'
    
    # if output file exists, write over it
    if os.path.exists(output_file):
        os.remove(output_file)

    for entry in data['HOTTP_Entries']['HOTTP_Entry']:
        refs = entry['References']['Reference']

        with open(output_file, 'a') as f:
            # write the refs array, \t, and then a json dump of the entry
            entry_json = json.dumps(entry, ensure_ascii=False)
            f.write(f'{refs}\t{entry_json}\n')

for file in os.listdir('.'):
    if file.endswith('.json'):
        process_json_file(file)
