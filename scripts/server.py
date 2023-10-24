from flask import Flask, request, jsonify
from clickhouse_driver import Client
import os

app = Flask(__name__)
client = Client('localhost')

def list_files(directory, extensions):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(tuple(extensions)):
                yield os.path.join(root, file).replace(directory, '')

def sanitize_input(input_string):
    return input_string.replace("'", "''")

valid_extensions = ['.jsonl', '.json', '.tsv', '.csv', '.txt']
sandbox_path = '/root/user_files/'
available_files = list(list_files(sandbox_path, valid_extensions))

@app.route('/query', methods=['GET'])
def query_clickhouse():
    table = request.args.get('file')
    search_string = request.args.get('search_string', '')
    column_name = request.args.get('column', '')
    limit = request.args.get('limit', 5)

    # Sanitize input
    search_string = sanitize_input(search_string)
    column_name = sanitize_input(column_name)

    # Validate the table
    if table not in available_files:
        return jsonify({"error": "File not found", "available_files": available_files})
    
    # To get the true column names, query the first result limit 1, then return values, and use these to map to `c1`, `c2`, etc.
    # This is a hacky way to get the column names, but it works for now
    column_name_string = '''xml:id Nullable(String), ref Nullable(String), class Nullable(String), \
text Nullable(String), transliteration Nullable(String), after Nullable(String), strongnumberx Nullable(String), \
stronglemma Nullable(String), sensenumber Nullable(String), greek Nullable(String), greekstrong Nullable(String), \
gloss Nullable(String), english Nullable(String), mandarin Nullable(String), stem Nullable(String), \
morph Nullable(String), lang Nullable(String), lemma Nullable(String), pos Nullable(String), person Nullable(String), \
gender Nullable(String), number Nullable(String), state Nullable(String), type Nullable(String), \
lexdomain Nullable(String), contextualdomain Nullable(String), coredomain Nullable(String), sdbh Nullable(String), \
extends Nullable(String), frame Nullable(String), subjref Nullable(String), participantref Nullable(String), \
role Nullable(String), normalized Nullable(String), strong Nullable(String), case Nullable(String), \
tense Nullable(String), voice Nullable(String), mood Nullable(String), degree Nullable(String), domain Nullable(String), \
ln Nullable(String), referent Nullable(String), vref Nullable(String), VREF Nullable(String), \
TEXT Nullable(String), marble_ids Nullable(String)'''
    
    try:
        # Prepare the query
        query = f"SELECT * FROM file('{sandbox_path}{table}', 'TSV', {column_name_string})"

        # Add a WHERE clause if a search_string and column_name are provided
        if search_string and column_name:
            query += f" WHERE {column_name} = '{search_string}'"

        # Add a LIMIT clause to limit the results
        query += f" LIMIT {limit}"

        # Execute the query
        result = client.execute(query)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


