import json
import sys

def rename_ambiguous_keys(obj, parent_key=''):
    obj_copy = obj.copy()  # Create a copy of the object to iterate over
    for key, value in obj_copy.items():
        new_key = f'{parent_key}-{key}' if parent_key else key  # Appending parent key to the current key
        
        if isinstance(value, dict):
            obj[new_key] = rename_ambiguous_keys(value, new_key)  # Recursion for nested dictionaries
            if new_key != key:  # Removing the old key if a new key was created
                del obj[key]
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            obj[new_key] = [rename_ambiguous_keys(item, new_key) for item in value]  # Recursion for list of dictionaries
            if new_key != key:  # Removing the old key if a new key was created
                del obj[key]

    return obj

def process_jsonl_file(input_filename, output_filename):
    with open(input_filename, 'r') as infile, open(output_filename, 'w') as outfile:
        # Read and process each line
        updated_lines = [rename_ambiguous_keys(json.loads(line)) for line in infile]
        # Write updated data to the output file
        for updated_obj in updated_lines:
            outfile.write(json.dumps(updated_obj) + '\n')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python rename_keys.py <input_filename> <output_filename>")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    process_jsonl_file(input_filename, output_filename)
