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
        entry_json = json.dumps(entry, ensure_ascii=False)
        ref_value = json.dumps(refs if isinstance(refs, list) else [refs], ensure_ascii=False)

        # replace tab and newline characters
        ref_value = ref_value.replace('\t', '\\t').replace('\n', '\\n')
        entry_json = entry_json.replace('\t', '\\t').replace('\n', '\\n')

        with open(output_file, 'a') as f:
            f.write(f'{ref_value}\t{entry_json}\n')

for file in os.listdir('.'):
    if file.endswith('.json'):
        process_json_file(file)
