from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime

# dbインスタンスの作成
db = SQLAlchemy()

class Telegram(db.Model):
    __tablename__ = 'telegrams'

    # Primary Key 文書番号
    # content.order_info.doc_id からセット
    id_ = Column(String(30), primary_key=True, comment='doc_id')

    # 検索用主要カラム (parserの抽出結果からapp.pyでセットされる)
    # content.patient_info.id からセット
    patient_id = Column(String(20), index=True, comment='Patient ID')
    # content.patient_info.kanji_name からセット
    patient_name = Column(String(100), comment='Patient Kanji Name')
    # content.order_info.number からセット
    order_number = Column(Integer, comment='Order Number')
    # content.order_info.version からセット
    order_version = Column(Integer, comment='Order Version')
    # content.order_info.sakusei_datetime.date からセット
    order_date = Column(String(20), comment='Order Date (YYYYMMDD)')

    # 解析した全データをJSONとして保存
    raw_data = Column(JSON, comment='Parsed Raw JSON Data')

    created_at = Column(DateTime, default=datetime.now, comment='Created At')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='Updated At')

    # Pythonの予約語id()と衝突しないようにするためのgetter
    def get_id(self):
        return self.id_

    def to_dict(self):
        """APIレスポンス用辞書変換"""
        return {
            'id': self.id_,
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'order_number': self.order_number,
            'order_version': self.order_version,
            'order_date': self.order_date,
            'raw_data': self.raw_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }