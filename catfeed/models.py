from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from catfeed import db

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CatProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    birthday = db.Column(db.Date)
    target_weight = db.Column(db.Float)
    daily_calories = db.Column(db.Integer)
    meals_per_day = db.Column(db.Integer)
    weight = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class FeedingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    feeder_nickname = db.Column(db.String(50), nullable=False, default='訪客')
    food_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Integer)
    notes = db.Column(db.String(200))
    session_id = db.Column(db.String(36))
    cat_id = db.Column(db.Integer, db.ForeignKey('cat_profile.id'))
    cat = db.relationship('CatProfile', backref=db.backref('feeding_records', lazy=True))

    @property
    def can_edit(self):
        """檢查記錄是否可以編輯（15分鐘內）"""
        if not self.timestamp:
            return False
        delta = datetime.utcnow() - self.timestamp
        return delta.total_seconds() <= 900  # 15 minutes

    def to_dict(self):
        local_time = self.timestamp.replace(tzinfo=None) + timedelta(hours=8)  # UTC+8
        return {
            'id': self.id,
            'timestamp': local_time.strftime('%Y-%m-%d %H:%M:%S'),
            'feeder_nickname': self.feeder_nickname,
            'food_type': self.food_type,
            'amount': self.amount,
            'calories': self.calories,
            'notes': self.notes,
            'can_edit': self.can_edit
        }

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(128))
    exif_data = db.Column(db.JSON)
    is_approved = db.Column(db.Boolean, default=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    cat_id = db.Column(db.Integer, db.ForeignKey('cat_profile.id'))
    cat = db.relationship('CatProfile', backref=db.backref('photos', lazy=True))

# 為了 Flask-Login 的相容性，將 Admin 別名為 User
User = Admin
