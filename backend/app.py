import os
import json
import tempfile
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError

# モデルとDBインスタンスをインポート
from models import db, Telegram
# パーサーをインポート
from parser import TelegramParser

app = Flask(__name__)
CORS(app)

# --- 設定 ---
DB_USER = os.environ.get('DB_USER', 'user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'userpassword')
DB_HOST = os.environ.get('DB_HOST', 'db')
DB_NAME = os.environ.get('DB_NAME', 'drug_order_db')

# SQLAlchemy設定 (mysql-connector-pythonを使用)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DBとMigrateの初期化
db.init_app(app)
migrate = Migrate(app, db)

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

def clean_numpy_data(data):
    """
    Numpy型を含む辞書を標準的なPython型(JSON化可能)な辞書に変換する。
    SQLAlchemy経由でMySQLに保存する際、NaNが含まれているとエラーになるため
    ここで None (null) に変換を行う。
    """
    # 1. まずNumpy型を標準型へダンプ (この時点で np.nan は "NaN" という文字列リテラルになる)
    json_str = json.dumps(data, cls=NumpyJSONEncoder)

    # 2. JSON文字列を辞書に戻す際、parse_constantフックを使って "NaN" を None に変換する
    return json.loads(json_str, parse_constant=lambda x: None if x == 'NaN' else float(x))

def save_parsed_data(parsed_data):
    """
    解析済みの辞書データをDBに保存する共通関数
    
    Returns:
        Telegram: 保存されたモデルインスタンス
    Raises:
        IntegrityError: 重複データが存在する場合
        Exception: その他のDBエラー
    """
    # 3. 必要な情報を抽出
    content = parsed_data.get('content', {})

    patient_info = content.get('patient_info', {})
    order_info = content.get('order_info', {})

    # 日付情報の抽出
    order_date_obj = order_info.get('sakusei_datetime', {})
    order_date = order_date_obj.get('date') if isinstance(order_date_obj, dict) else None

    # 4. モデル作成と保存
    # JSON型カラムに入れるためにデータをクリーンアップ
    cleaned_data = clean_numpy_data(parsed_data)

    new_telegram = Telegram(
        doc_id=order_info.get('doc_id'),
        version=order_info.get('version'),
        patient_id=patient_info.get('id'),
        patient_name=patient_info.get('kanji_name'),
        order_number=order_info.get('number'),
        order_date=order_date,
        raw_data=cleaned_data
    )

    db.session.add(new_telegram)
    db.session.commit()
    
    return new_telegram

# --- APIエンドポイント ---

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Backend is running with ORM"})

@app.route('/api/telegrams/receive', methods=['POST'])
def receive_telegram():
    """
    【新規】システム連携用: 電文データをバイナリで直接受信するエンドポイント
    curl -X POST --data-binary @file.dat ... 等で利用
    """
    # 生のバイト列を取得
    raw_bytes = request.get_data()
    
    if not raw_bytes:
        return jsonify({"error": "No data received"}), 400

    try:
        # 1. 解析実行 (バイト列を直接渡す)
        # 改修後のTelegramParserはbytesを受け取れる想定
        parser = TelegramParser(raw_bytes, encoding='cp932')
        parsed_data = parser.parse()

        # 2. DB保存 (共通関数を使用)
        new_telegram = save_parsed_data(parsed_data)

        return jsonify({
            "message": "Telegram received and saved successfully",
            "id": new_telegram.id_,
            "doc_id": new_telegram.doc_id,
            "version": new_telegram.version,
            "patient_name": new_telegram.patient_name
        }), 201

    except ValueError as ve:
        # 解析エラー (フォーマット不正など)
        return jsonify({"error": f"Validation Error: {str(ve)}"}), 400
        
    except IntegrityError:
        # 重複エラー (doc_id + version が既に存在)
        db.session.rollback()
        return jsonify({"error": "Conflict: This telegram already exists."}), 409

    except Exception as e:
        db.session.rollback()
        print(f"Error processing telegram: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    ファイルをアップロードし、解析してDBに保存する
    (Reactフロントエンド用)
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    temp_path = None
    try:
        # 1. 一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            file.save(temp.name)
            temp_path = temp.name

        # 2. 解析実行 (ファイルパスを渡す)
        parser = TelegramParser(temp_path, encoding='cp932')
        parsed_data = parser.parse()

        # 3. DB保存 (共通関数を使用)
        new_telegram = save_parsed_data(parsed_data)

        return jsonify({
            "message": "File parsed and saved successfully",
            "id": new_telegram.id_,
            "patient_name": new_telegram.patient_name
        }), 201
    
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "この電文は既に登録されています。"}), 409

    except Exception as e:
        print(f"Error processing file: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/api/telegrams', methods=['GET'])
def get_telegrams():
    """
    保存された電文リストを取得する
    """
    try:
        # 作成日時の降順で取得
        telegrams = Telegram.query.order_by(Telegram.created_at.desc()).all()

        # 一覧用に軽量なデータを返す
        results = []
        for t in telegrams:
            results.append({
                "id": t.id_,
                "doc_id": t.doc_id,
                "version": t.version,
                "patient_id": t.patient_id,
                "patient_name": t.patient_name,
                "order_number": t.order_number,
                "order_date": t.order_date,
                "created_at": t.created_at
            })

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/telegrams/<string:telegram_id>', methods=['GET'])
def get_telegram_detail(telegram_id):
    """
    特定の電文の詳細を取得する
    """
    try:
        telegram = db.session.get(Telegram, telegram_id)
        if not telegram:
             return jsonify({"error": "Not found"}), 404

        # to_dict() ヘルパーを使用
        return jsonify(telegram.to_dict())

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)