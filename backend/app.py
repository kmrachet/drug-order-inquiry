import os
import json
import tempfile
import numpy as np
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS

# 同ディレクトリにある parser.py をインポート
from parser import TelegramParser

app = Flask(__name__)
# フロントエンド(React)からのアクセスを許可
CORS(app)

# --- 設定 ---
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'db'),
    'user': os.environ.get('DB_USER', 'user'),
    'password': os.environ.get('DB_PASSWORD', 'userpassword'),
    'database': os.environ.get('DB_NAME', 'drug_order_db'),
    'port': 3306
}

# --- ヘルパー: Numpy対応JSONエンコーダ ---
class NumpyJSONEncoder(json.JSONEncoder):
    """
    parser.py が返すデータに含まれる np.nan などを
    JSON規格(null)に変換するためのエンコーダ
    """
    def default(self, obj):
        if isinstance(obj, float) and np.isnan(obj):
            return None
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

app.json_encoder = NumpyJSONEncoder

# --- データベース接続 ---
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    """テーブルが存在しない場合に作成する"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # MySQL 8.0のJSON型を利用して、構造が変わっても柔軟に対応できるようにする
        # patient_name などの頻繁に検索しそうな項目はカラムとして独立させる
        create_table_query = """
        CREATE TABLE IF NOT EXISTS telegrams (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id VARCHAR(20),
            patient_name VARCHAR(100),
            order_date VARCHAR(20),
            raw_data JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
    finally:
        if conn:
            conn.close()

# アプリ起動時にDB初期化を実行 (本番環境ではmigrationツール推奨)
with app.app_context():
    init_db()

# --- APIエンドポイント ---

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Backend is running"})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    ファイルをアップロードし、解析してDBに保存する
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    temp_path = None
    try:
        # 1. 一時ファイルとして保存 (parserがファイルパスを要求するため)
        # delete=False にして、あとで手動削除する
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            file.save(temp.name)
            temp_path = temp.name

        # 2. 解析実行
        parser = TelegramParser(temp_path, encoding='cp932')
        parsed_data = parser.parse()

        # 3. 必要な情報を抽出
        content = parsed_data.get('content', {})
        patient_info = content.get('patient_info', {})
        order_info = content.get('order_info', {})
        
        # np.nan 対策をして辞書化
        data_json = json.dumps(parsed_data, cls=NumpyJSONEncoder)
        
        patient_id = patient_info.get('kanja_bangou')
        patient_name = patient_info.get('kanja_kanji_shimei')
        
        # 日付情報の抽出 (order_sakusei_date.date など)
        order_date_obj = order_info.get('order_sakusei_date', {})
        order_date = order_date_obj.get('date') if isinstance(order_date_obj, dict) else None

        # 4. DBへ保存
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO telegrams (patient_id, patient_name, order_date, raw_data)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (patient_id, patient_name, order_date, data_json))
        
        new_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": "File parsed and saved successfully",
            "id": new_id,
            "patient_name": patient_name
        }), 201

    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        # 一時ファイルの削除
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/api/telegrams', methods=['GET'])
def get_telegrams():
    """
    保存された電文リストを取得する
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) # 結果を辞書形式で取得
        
        # 一覧表示に必要な軽い情報だけ取得
        query = "SELECT id, patient_id, patient_name, order_date, created_at FROM telegrams ORDER BY created_at DESC"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/telegrams/<int:telegram_id>', methods=['GET'])
def get_telegram_detail(telegram_id):
    """
    特定の電文の詳細(JSON全文)を取得する
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM telegrams WHERE id = %s"
        cursor.execute(query, (telegram_id,))
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            # raw_data は MySQL Connector によって既に文字/辞書になっている場合があるが
            # 必要に応じて parse する (JSON型カラムの場合は自動変換されることが多い)
            if isinstance(row['raw_data'], str):
                row['raw_data'] = json.loads(row['raw_data'])
            return jsonify(row)
        else:
            return jsonify({"error": "Not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)