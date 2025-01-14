from catfeed import db
from datetime import datetime

class FeedingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)  # in grams
    food_type = db.Column(db.String(50), nullable=False)
    calories = db.Column(db.Integer)
    notes = db.Column(db.Text)
    feeder_nickname = db.Column(db.String(50), nullable=False)
    session_id = db.Column(db.String(100))  # 用於追蹤訪客的記錄
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'amount': self.amount,
            'food_type': self.food_type,
            'calories': self.calories,
            'notes': self.notes,
            'feeder_nickname': self.feeder_nickname,
            'session_id': self.session_id,
            'can_edit': self.can_edit()
        }
    
    def can_edit(self):
        """檢查記錄是否可以編輯（15分鐘內）"""
        if not self.timestamp:
            return False
        return (datetime.utcnow() - self.timestamp).total_seconds() < 900  # 15分鐘 = 900秒
