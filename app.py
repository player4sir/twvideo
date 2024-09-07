from flask import Flask, jsonify, request
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

app = Flask(__name__)

# Parse the DATABASE_URL
DATABASE_URL = os.environ.get('DATABASE_URL')
url = urlparse(DATABASE_URL)

# Connect to PostgreSQL using parsed components
conn = psycopg2.connect(
    dbname=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port,
    sslmode='require'
)

# Create table if not exists


def create_table():
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gpts_data (
                title TEXT PRIMARY KEY,
                profile_picture TEXT,
                welcome_message TEXT,
                description TEXT,
                prompt_starters TEXT[],
                system_prompt TEXT
            )
        """)
    conn.commit()

# Load data from PostgreSQL


def load_data():
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM gpts_data")
        return cur.fetchall()

# Save data to PostgreSQL


def save_data(data):
    create_table()  # Ensure table exists before saving data
    with conn.cursor() as cur:
        cur.execute("DELETE FROM gpts_data")
        for item in data:
            cur.execute("INSERT INTO gpts_data (title, profile_picture, welcome_message, description, prompt_starters, system_prompt) VALUES (%s, %s, %s, %s, %s, %s)",
                        (item['title'], item['profile_picture'], item['welcome_message'], item['description'], item['prompt_starters'], item['system_prompt']))
    conn.commit()

# Get all data


@app.route('/api/data', methods=['GET'])
def get_all_data():
    data = load_data()
    return jsonify(data)

# Get data by title


@app.route('/api/data/<string:title>', methods=['GET'])
def get_data_by_title(title):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM gpts_data WHERE title = %s", (title,))
        item = cur.fetchone()
    if item:
        return jsonify(item)
    return jsonify({"error": "Item not found"}), 404

# Add new data


@app.route('/api/data', methods=['POST'])
def add_data():
    new_item = request.json
    create_table()  # Ensure table exists before adding data
    with conn.cursor() as cur:
        cur.execute("INSERT INTO gpts_data (title, profile_picture, welcome_message, description, prompt_starters, system_prompt) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *",
                    (new_item['title'], new_item['profile_picture'], new_item['welcome_message'], new_item['description'], new_item['prompt_starters'], new_item['system_prompt']))
        inserted_item = cur.fetchone()
    conn.commit()
    return jsonify(inserted_item), 201

# Update existing data


@app.route('/api/data/<string:title>', methods=['PUT'])
def update_data(title):
    update_data = request.json
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("UPDATE gpts_data SET profile_picture = %s, welcome_message = %s, description = %s, prompt_starters = %s, system_prompt = %s WHERE title = %s RETURNING *",
                    (update_data['profile_picture'], update_data['welcome_message'], update_data['description'], update_data['prompt_starters'], update_data['system_prompt'], title))
        updated_item = cur.fetchone()
    conn.commit()
    if updated_item:
        return jsonify(updated_item)
    return jsonify({"error": "Item not found"}), 404

# Delete data


@app.route('/api/data/<string:title>', methods=['DELETE'])
def delete_data(title):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM gpts_data WHERE title = %s RETURNING *", (title,))
        deleted_item = cur.fetchone()
    conn.commit()
    if deleted_item:
        return jsonify({"message": "Item deleted successfully"})
    return jsonify({"error": "Item not found"}), 404

# Import data from dt.json
# @app.route('/api/import', methods=['POST'])
# def import_data():
#     try:
#         with open('dt.json', 'r', encoding='utf-8') as file:
#             data = json.load(file)
#         save_data(data)
#         return jsonify({"message": "Data imported successfully"}), 200
#     except json.JSONDecodeError as e:
#         return jsonify({"error": f"Invalid JSON format: {str(e)}"}), 400
#     except FileNotFoundError:
#         return jsonify({"error": "dt.json file not found"}), 404
#     except Exception as e:
#         return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# Create table on startup
create_table()

# Remove debug mode for production
if __name__ == '__main__':
    app.run(debug=False, port=5000)
