from catfeed import db
from datetime import datetime

class CatProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=True)  
    birthday = db.Column(db.Date)
    weight = db.Column(db.Float)
    target_weight = db.Column(db.Float)
    daily_calories = db.Column(db.Integer)
    meals_per_day = db.Column(db.Integer)
    neutered = db.Column(db.Boolean, default=False)
    activity_level = db.Column(db.String(20))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'birthday': self.birthday.isoformat() if self.birthday else None,
            'weight': self.weight,
            'target_weight': self.target_weight,
            'daily_calories': self.daily_calories,
            'meals_per_day': self.meals_per_day,
            'neutered': self.neutered,
            'activity_level': self.activity_level,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
