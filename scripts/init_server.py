from time import sleep
from clickhouse_driver import Client
import os

client = Client('localhost')

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

def initialize_clickhouse():
    sleep(5) # wait for clickhouse to start
    all_jsonl_files = [f for f in available_files if f.endswith('.jsonl')]
    translations = [f.split('/')[1] for f in all_jsonl_files]
    
    tables = client.execute("SHOW TABLES")
    print('Existing tables:', tables)
    
    if 'macula' in tables and 'marble_macula_mappings' and all(f'{translation}_alignment' in tables for translation in translations):
        print('Tables already exist, skipping initialization')
        return
    
    # Create the tables # FIXME: we need to move this out into a separate script that runs on startup, otherwise it will run with four workers and happen four times.
    # try dropping the macula table first
    try:
        client.execute('DROP TABLE IF EXISTS macula')
    except Exception as e:
        print(f"Could not drop macula table: {e}")
        print('Continuing with initialization...')
    
    try:
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS macula ({macula_column_name_string}) ENGINE = MergeTree()
        PRIMARY KEY (VREF);
        """
        print('Creating macula table')
        client.execute(create_table_query)
    except Exception as e:
        print(f"Could not create table: {e}")
    # Insert data from TSV file
    try:
        insert_data_query = f"""
        INSERT INTO macula
        SELECT *
        FROM file('macula/macula-with-marble-ids.tsv', 'TSV', '{macula_column_name_string}');
        """
        print('Inserting data from TSV file')
        client.execute(insert_data_query)
    except Exception as e:
        print(f"Could not insert data from TSV file: {e}")
        
    # Insert data from JSONL files prepended with vref values, making them tsvs
    print(f"Found {len(all_jsonl_files)} JSONL files", all_jsonl_files)
    
    for jsonl_file in all_jsonl_files:        
        # turn all escaped double quotes into single quotes in the file globally
        with open(os.path.join(sandbox_path, jsonl_file), 'r') as f:
            print(f"Escaping double quotes in {jsonl_file}")
            data = f.read()
            data = data.replace('\\"', "'")
        with open(os.path.join(sandbox_path, jsonl_file), 'w') as f:
            f.write(data)
        
        translation = jsonl_file.split('/')[1]
        table_name = f'{translation}_alignment'
        try:
            client.execute(f'DROP TABLE IF EXISTS {table_name}')
        except:
            pass

        try: 
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                vref String,
                json_data String
            ) ENGINE = MergeTree()
            ORDER BY vref
            SETTINGS allow_nullable_key = 1;
            """
            print('Creating alignments table')
            client.execute(create_table_query, settings={
                'allow_experimental_object_type': 1,
                'namedtuple_as_json': False
            })
        except Exception as e:
            print(f"Could not create table: {e}")

        
        try:
            insert_data_query = f"""
            INSERT INTO {table_name}
            SELECT *
            FROM file('{jsonl_file}', 'TSV', 'vref String, json_data String');
            """
            print('Inserting data from JSONL files')
            client.execute(insert_data_query, settings={
                'allow_experimental_object_type': 1,
                'namedtuple_as_json': False
            })
        except Exception as e:
            print(f"Could not insert data from JSONL files: {e}")
            
    all_hottp_tsv_files = [f for f in available_files if 'hottp' in f and f.endswith('.tsv')]
    print(f"Found {len(all_hottp_tsv_files)} HOTTP TSV files", all_hottp_tsv_files)
    
    for hottp_tsv_file in all_hottp_tsv_files:
        # turn all escaped double quotes into single quotes in the file globally
        with open(os.path.join(sandbox_path, hottp_tsv_file), 'r') as f:
            print(f"Escaping double quotes in {hottp_tsv_file}")
            data = f.read()
            data = data.replace('\\"', "'")
        with open(os.path.join(sandbox_path, hottp_tsv_file), 'w') as f:
            f.write(data)
        
        # hottp/HOTTP_translated_spa_Latn.tsv --> spa_Latn
        hottp_translation = '_'.join(hottp_tsv_file.split('/')[1].split('_')[-2:]).split('.')[0] # FIXME: this is a stupid way for me to have done this.
        hottp_table_name = f'hottp_{hottp_translation}'
        try:
            client.execute(f'DROP TABLE IF EXISTS {hottp_table_name}')
        except:
            pass

        try: 
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {hottp_table_name} (
                refArray Array(String),
                json_data String
            ) ENGINE = MergeTree()
            ORDER BY refArray;
            """
            print('Creating HOTTP table')
            client.execute(create_table_query, settings={
                'allow_experimental_object_type': 1,
                'namedtuple_as_json': False
            })
        except Exception as e:
            print(f"Could not create table: {e}")

        
        try:
            insert_data_query = f"""
            INSERT INTO {hottp_table_name}
            SELECT *
            FROM file('{hottp_tsv_file}', 'TSV', 'refs Array(String), json_data String');
            """
            print('Inserting data from HOTTP TSV files')
            client.execute(insert_data_query, settings={
                'allow_experimental_object_type': 1,
                'namedtuple_as_json': False
            })
        except Exception as e:
            print(f"Could not insert data from HOTTP TSV files: {e}")

    # Create a table from mappings/marble-macula-id-mappings.csv, with type "CSV" and columns maculaId String, marbleId String
    try:
        marble_macula_table_name = 'marble_macula_mappings'
        client.execute(f'DROP TABLE IF EXISTS {marble_macula_table_name}')
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {marble_macula_table_name} (
            maculaId String,
            marbleId String
        ) ENGINE = MergeTree()
        ORDER BY maculaId;
        """
        print('Creating marble-macula mappings table')
        client.execute(create_table_query)
        insert_data_query = f"""
        INSERT INTO {marble_macula_table_name}
        SELECT *
        FROM file('mappings/marble-macula-id-mappings.csv', 'CSV', 'maculaId String, marbleId String');
        """
        print('Inserting data from marble-macula mappings CSV file')
        client.execute(insert_data_query)
    except Exception as e:
        print(f"Could not create or insert data into marble-macula mappings table: {e}")
    # # Create the index (assuming you want to create an index on column1)
    # try:
    #     create_index_query_xmlid = """
    #     CREATE INDEX IF NOT EXISTS xmlid_index
    #     ON macula(xmlid) TYPE minmax;
    #     """
    #     print('Creating index on `xmlid` column')
    #     client.execute(create_index_query_xmlid)
    #     create_index_query_VREF = """
    #     CREATE INDEX IF NOT EXISTS VREF_index
    #     ON macula(VREF) TYPE minmax;
    #     """
    #     print('Creating index on `VREF` column')
    #     client.execute(create_index_query_VREF)
    # except Exception as e:
    #     print(f"Could not create index: {e}")
    
    print('Done initializing ClickHouse!')
    
if __name__ == '__main__':
    initialize_clickhouse()