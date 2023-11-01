from flask import Flask, request, jsonify
from clickhouse_driver import Client
import os
from flask_httpauth import HTTPTokenAuth
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://text-librarian.vercel.app/"])
auth = HTTPTokenAuth(scheme='Bearer')
client = Client('localhost')
SECRET_KEY = os.environ.get('SECRET_AUTH_KEY')

@auth.verify_token
def verify_token(token):
    return token == SECRET_KEY

def list_files(directory, extensions):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(tuple(extensions)):
                yield os.path.join(root, file).replace(directory, '')

def sanitize_input(input_string):
    return input_string.replace("'", "''")

valid_extensions = ['.jsonl', '.json', '.tsv', '.csv', '.txt']
sandbox_path = '/root/user_files/' if os.path.exists('/root/user_files/') else '../../user_files/'
available_files = list(list_files(sandbox_path, valid_extensions))
print('available_files', available_files)
macula_column_name_string = '''`xmlid` Nullable(String), `ref` Nullable(String), `class` Nullable(String), `text` Nullable(String), `transliteration` Nullable(String), `after` Nullable(String), `strongnumberx` Nullable(String), `stronglemma` Nullable(String), `sensenumber` Nullable(String), `greek` Nullable(String), `greekstrong` Nullable(String), `gloss` Nullable(String), `english` Nullable(String), `mandarin` Nullable(String), `stem` Nullable(String), `morph` Nullable(String), `lang` Nullable(String), `lemma` Nullable(String), `pos` Nullable(String), `person` Nullable(String), `gender` Nullable(String), `number` Nullable(String), `state` Nullable(String), `type` Nullable(String), `lexdomain` Nullable(String), `contextualdomain` Nullable(String), `coredomain` Nullable(String), `sdbh` Nullable(String), `extends` Nullable(String), `frame` Nullable(String), `subjref` Nullable(String), `participantref` Nullable(String), `role` Nullable(String), `normalized` Nullable(String), `strong` Nullable(String), `case` Nullable(String), `tense` Nullable(String), `voice` Nullable(String), `mood` Nullable(String), `degree` Nullable(String), `domain` Nullable(String), `ln` Nullable(String), `referent` Nullable(String), `vref` Nullable(String), `VREF` String, `TEXT` Nullable(String), `marble_ids` Nullable(String)'''

macula_column_names = [
            "xmlid",
            "ref",
            "class",
            "text",
            "transliteration",
            "after",
            "strongnumberx",
            "stronglemma",
            "sensenumber",
            "greek",
            "greekstrong",
            "gloss",
            "english",
            "mandarin",
            "stem",
            "morph",
            "lang",
            "lemma",
            "pos",
            "person",
            "gender",
            "number",
            "state",
            "type",
            "lexdomain",
            "contextualdomain",
            "coredomain",
            "sdbh",
            "extends",
            "frame",
            "subjref",
            "participantref",
            "role",
            "normalized",
            "strong",
            "case",
            "tense",
            "voice",
            "mood",
            "degree",
            "domain",
            "ln",
            "referent",
            "vref",
            "VREF",
            "TEXT",
            "marble_ids"
        ]

@app.route('/query', methods=['GET'])
@auth.login_required
def query_clickhouse():
    table = request.args.get('file')
    search_string = request.args.get('search_string', '')
    column_name = request.args.get('column_name', '')
    limit = request.args.get('limit', 5)

    # Sanitize input
    search_string = sanitize_input(search_string)
    column_name = sanitize_input(column_name)

    # Validate the table
    if table not in available_files:
        return jsonify({"error": "File not found", "available_files": available_files, "cwd": os.getcwd()})
    
    try:
        # Prepare the query
        query = f"SELECT * FROM file('{sandbox_path}{table}', 'TSV', '{macula_column_name_string}')"

        # Add a WHERE clause if a search_string and column_name are provided
        if search_string and column_name:
            query += f" WHERE {column_name} = '{search_string}'"

        # Add a LIMIT clause to limit the results
        query += f" LIMIT {limit}"

        # Execute the query
        result = client.execute(query)
        return jsonify({'result': result, "request": {"table": table, "search_string": search_string, "column_name": column_name, "limit": limit}})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/macula', methods=['GET']) # FIXME: the macula table is not consistently compressing data or something. Queries fail every time currently. Alignments table seems to work fine.
@auth.login_required
def query_macula():
    search_string = request.args.get('search_string', '')
    column_name = request.args.get('column_name', '')
    limit = request.args.get('limit', 5)

    # Sanitize input
    search_string = sanitize_input(search_string)
    column_name = sanitize_input(column_name)

    try:
        # Prepare the query
        query = "SELECT * FROM macula"

        # Add a WHERE clause if a search_string and column_name are provided
        if search_string and column_name:
            query += f" WHERE {column_name} = '{search_string}'"

        # Add a LIMIT clause to limit the results
        query += f" LIMIT {limit}"

        # Execute the query
        result = client.execute(query)
        return jsonify({'result': result, "request": {"search_string": search_string, "column_name": column_name, "limit": limit}})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/alignments', methods=['GET'])
@auth.login_required
def query_alignments():
    vref = request.args.get('vref', '')
    limit = request.args.get('limit', 5)
    translation = request.args.get('nllb_language_code', 'spa_Latn') # TODO: add some helpful error handling here. Need to use flores NLLB codes
    
    try:
        # Prepare the query
        table_name = f'{translation}_alignment'
        query = f"SELECT * FROM {table_name}"

        # Add a WHERE clause if a search_string and column_name are provided
        if vref:
            query += f" WHERE vref = '{vref}'"

        # Add a LIMIT clause to limit the results
        query += f" LIMIT {limit}"

        # Execute the query
        result = client.execute(query)
        return jsonify({'result': result, "request": {"vref": vref, "limit": limit}})
    except Exception as e:
        return jsonify({'error': str(e)})

# endpoint to get 1 passage worth of alignments and macula rows 
@app.route('/passage', methods=['GET'])
@auth.login_required
def query_passage():
    book = request.args.get('book', '') # e.g., GEN, ROM, 
    chapter = request.args.get('chapter', '') 
    verse = request.args.get('verse', '%') # NOTE: vref is '%' by default so that it can be a wildcard if not provided as arg
    translation = request.args.get('translation', 'spanish')
    
    if not book or not chapter:
        return jsonify({'error': 'Please provide a `book` and `chapter` (and optionally `verse`) arg'})
    
    try:
        # Prepare the query for alignments
        table_name_alignments = f'{translation}_alignment'
        query_alignments = f"""
        SELECT * FROM {table_name_alignments}
        WHERE vref LIKE '{book} {chapter}:{verse}'
        """

        # Execute the query for alignments
        result_alignments = client.execute(query_alignments)

        # Prepare the query for macula
        table_name_macula = 'macula'
        query_macula = f"""
        SELECT * FROM {table_name_macula}
        WHERE vref LIKE '{book} {chapter}:{verse}'
        """

        # Execute the query for macula
        result_macula = client.execute(query_macula)
        
        # Return both results
        return jsonify({'alignments': result_alignments, 'macula': result_macula, 'macula_column_names': macula_column_names})
    except Exception as e:
        return jsonify({'error': str(e)})
    
# endpoint to get hottp data when a given ref is in the refArray
@app.route('/hottp', methods=['GET'])
@auth.login_required
def query_hottp():
    marbleRef = request.args.get('marbleRef', '') # NOTE: can be a partial or complete marbleRef. The beginning of the ID must be complete. The end can be truncated.
    # limit = request.args.get('limit', 5)
    translation = request.args.get('translation', 'spa_Latn')
    try:
        # Prepare the query
        table_name = f'hottp_{translation}'
        query = f"SELECT * FROM {table_name}"

        # Add a WHERE clause if a marbleRef
        if not marbleRef:
            return jsonify({'error': 'Please provide a marbleRef arg (i.e., a UBS Marble project ID)'})
    
        query += f" WHERE arrayExists(x -> x LIKE '{marbleRef}%', refArray)"

        # Add a LIMIT clause to limit the results
        # query += f" LIMIT {limit}"

        # Execute the query
        result = client.execute(query) #? TODO: should we json parse the stringified json_data before sending to frontend?
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/resolveId', methods=['GET'])
@auth.login_required
def resolve_id():
    id = request.args.get('id', '')
    if not id:
        return jsonify({'error': 'Please provide an id arg'})
    
    # Prepare the query
    table_name = 'marble_macula_mappings'
    query = f"""
    SELECT * FROM {table_name}
    WHERE maculaId LIKE '{id}%' OR marbleId LIKE '{id}%'
    """
    
    # Execute the query
    rows = client.execute(query)
    
    # Check if rows is empty
    if not rows:
        return jsonify({'error': 'No matching ids found'})
    
    result = [{'maculaId': row[0], 'marbleId': row[1]} for row in rows]
    
    # Return the rows
    return jsonify(result)

if __name__ == '__main__':
    print('Starting Flask server')
    app.run(host='0.0.0.0', port=5000)
