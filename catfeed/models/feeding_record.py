from catfeed import db
from datetime import datetime

class FeedingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    amount = db.Column(db.Float, nullable=False)  # in grams
    calories = db.Column(db.Integer)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'amount': self.amount,
            'calories': self.calories,
            'notes': self.notes
        }
