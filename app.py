import logging
from flask import Flask, jsonify, request
import os
import psycopg2
from psycopg2 import OperationalError

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def fetch_data(cursor, page_size, last_id=None):
    try:
        if last_id:
            cursor.execute(f"SELECT Id, Image_url, Variants FROM media_data WHERE Id > %s ORDER BY Id LIMIT %s;", (last_id, page_size))
        else:
            cursor.execute(f"SELECT Id, Image_url, Variants FROM media_data ORDER BY Id LIMIT %s;", (page_size,))
        
        rows = cursor.fetchall()

        # 格式化查询结果
        results = []
        for row in rows:
            id, image_url, variants = row
            result = {
                "Id": id,
                "Image_url": image_url,
                "Variants": variants
            }
            results.append(result)

        return results
    except OperationalError as e:
        logging.error("OperationalError: %s", e)
        return []
    except Exception as e:
        logging.error("Error: %s", e)
        return []

@app.route('/api', methods=['GET'])
def get_data():
    try:
        page_size = int(request.args.get('page_size', 10))
        page = int(request.args.get('page', 1))
        # 计算偏移量
        offset = (page - 1) * page_size
        # 从环境变量中读取数据库连接信息
        db_user = os.environ.get('POSTGRES_USER')
        db_password = os.environ.get('POSTGRES_PASSWORD')
        db_host = os.environ.get('POSTGRES_HOST')
        db_port = os.environ.get('POSTGRES_PORT')
        db_database = os.environ.get('POSTGRES_DATABASE')
        # 建立数据库连接
        conn = psycopg2.connect(
            dbname=db_database,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        # 创建游标对象
        cursor = conn.cursor()
        # 获取数据
        data = fetch_data(cursor, page_size, offset)
        # 关闭游标和连接
        cursor.close()
        conn.close()

        # 将数据转换为JSON格式并返回
        return jsonify(data), 200

    except ValueError as e:
        logging.error("ValueError: %s", e)
        return jsonify({"error": "Invalid input parameters"}), 400
    except Exception as e:
        logging.error("Error: %s", e)
        return jsonify({"error": "Internal Server Error"}), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
