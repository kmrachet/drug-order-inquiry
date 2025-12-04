from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime

# dbインスタンスの作成
db = SQLAlchemy()

class Telegram(db.Model):
    __tablename__ = 'telegrams'

    # 管理用ID
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 検索用主要カラム (parserの抽出結果からapp.pyでセットされる)
    patient_id = Column(String(20), index=True, comment='Patient ID')
    patient_name = Column(String(100), comment='Patient Kanji Name')
    order_date = Column(String(20), comment='Order Date (YYYYMMDD)')

    # 電文種別などのヘッダー情報
    system_code = Column(String(10), comment='Destination System Code')

    # 解析した全データをJSONとして保存
    raw_data = Column(JSON, comment='Parsed Raw JSON Data')

    created_at = Column(DateTime, default=datetime.now, comment='Created At')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='Updated At')

    def to_dict(self):
        """APIレスポンス用辞書変換"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'order_date': self.order_date,
            'raw_data': self.raw_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }