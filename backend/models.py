from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime

# dbインスタンスの作成
db = SQLAlchemy()

class Telegram(db.Model):
    __tablename__ = 'telegrams'

    # 管理用ID
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 検索用主要カラム (PDF定義の患者情報、オーダ情報より抜粋)
    patient_id = Column(String(20), index=True, comment='患者番号')
    patient_name = Column(String(100), comment='患者漢字氏名')
    order_date = Column(String(20), comment='オーダ日付(YYYYMMDD)')
    
    # 電文種別などのヘッダー情報（必要に応じて追加）
    system_code = Column(String(10), comment='送信先システムコード')

    # 解析した全データをJSONとして保存 (parser.pyのDotDict構造をそのまま格納)
    # これにより、PDFにある「項目情報群」などの複雑なネストも柔軟に保存可能
    raw_data = Column(JSON, comment='解析済み電文データ全文')

    created_at = Column(DateTime, default=datetime.now, comment='登録日時')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新日時')

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