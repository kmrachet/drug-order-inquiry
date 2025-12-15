from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime

# dbインスタンスの作成
db = SQLAlchemy()

class Telegram(db.Model):
    __tablename__ = 'telegrams'

    # Primary Key 文書番号
    id_ = Column(Integer, primary_key=True, autoincrement=True, comment='Primary Key')

    # 検索用主要カラム (parserの抽出結果からapp.pyでセットされる)
    # content.order_info.doc_id からセット
    doc_id = Column(String(30), comment='doc_id')
    # content.order_info.version からセット
    version = Column(Integer, comment='version')
    # 複合ユニークキー
    __table_args__ = (
        db.UniqueConstraint('doc_id', 'version', name='uix_doc_id_version'),
    )
    # content.patient_info.id からセット
    patient_id = Column(String(20), index=True, comment='Patient ID')
    # content.patient_info.kanji_name からセット
    patient_name = Column(String(100), comment='Patient Kanji Name')
    # content.order_info.number からセット
    order_number = Column(Integer, comment='Order Number')
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
            'doc_id': self.doc_id,
            'version': self.version,
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'order_number': self.order_number,
            'order_date': self.order_date,
            'raw_data': self.raw_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }