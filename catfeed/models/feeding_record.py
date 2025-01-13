from catfeed import db
from datetime import datetime

class FeedingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    food_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # in grams
    unit = db.Column(db.String(10))
    calories = db.Column(db.Integer)
    notes = db.Column(db.Text)
    feeder_nickname = db.Column(db.String(50), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'food_type': self.food_type,
            'amount': self.amount,
            'unit': self.unit,
            'calories': self.calories,
            'notes': self.notes,
            'feeder_nickname': self.feeder_nickname
        }
