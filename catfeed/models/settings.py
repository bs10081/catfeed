from .. import db

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timezone = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<Settings {self.id}>'
