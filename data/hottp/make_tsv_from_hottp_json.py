import json
import os
import csv

def process_json_file(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    filename = json_file.split('.')[0]
    output_file = f'{filename}.tsv'
    
    # if output file exists, write over it
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # Load the marble-macula mapping
    marble_macula_mapping = {}
    with open('../mappings/marble-macula-id-mappings.csv', 'r') as mapping_file:
        reader = csv.reader(mapping_file)
        next(reader)  # Skip the header
        for row in reader:
            marble_macula_mapping[row[1]] = row[0]

    for entry in data['HOTTP_Entries']['HOTTP_Entry']:
        refs = entry['References']['Reference'] # refs is a marble token id or an array of marble token ids
        entry_json = json.dumps(entry, ensure_ascii=False)
        ref_value = refs if isinstance(refs, list) else [refs]

        # Replace the ref_value with an array of matching Macula IDs
        ref_value = [marble_macula_mapping[ref] for ref in ref_value if ref in marble_macula_mapping]

        with open(output_file, 'a') as f:
            f.write(f'{ref_value}\t{entry_json}\n')

for file in os.listdir('.'):
    if file.endswith('.json'):
        process_json_file(file)
