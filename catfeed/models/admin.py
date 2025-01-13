from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from catfeed import db

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_login_success(self):
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        self.last_failed_login = None
        db.session.commit()
    
    def update_login_failure(self):
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()
        db.session.commit()
    
    def is_locked_out(self):
        if self.last_failed_login is None or self.failed_login_attempts < 5:
            return False
        lockout_duration = datetime.utcnow() - self.last_failed_login
        return lockout_duration.total_seconds() < 300  # 5 minutes lockout
