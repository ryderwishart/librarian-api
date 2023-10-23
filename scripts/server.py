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

    # Sanitize input
    search_string = sanitize_input(search_string)
    column_name = sanitize_input(column_name)

    # Validate the table
    if table not in available_files:
        return jsonify({"error": "File not found", "available_files": available_files})

    try:
        # Prepare the query
        query = f"SELECT * FROM file('{sandbox_path}{table}')"

        # Add a WHERE clause if a search_string and column_name are provided
        if search_string and column_name:
            query += f" WHERE {column_name} = '{search_string}'"

        # Add a LIMIT clause to limit the results to 50
        query += " LIMIT 50"

        # Execute the query
        result = client.execute(query)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


