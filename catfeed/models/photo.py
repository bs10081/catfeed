from catfeed import db
from datetime import datetime

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    file_size = db.Column(db.Integer)  # in bytes
    mime_type = db.Column(db.String(100))
    
    # EXIF 相關欄位
    date_taken = db.Column(db.DateTime)
    photographer = db.Column(db.String(100))
    description = db.Column(db.Text)
    camera_make = db.Column(db.String(100))
    camera_model = db.Column(db.String(100))
    exposure_time = db.Column(db.String(50))
    f_number = db.Column(db.Float)
    iso_speed = db.Column(db.Integer)
    focal_length = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'upload_date': self.upload_date.isoformat(),
            'is_approved': self.is_approved,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'date_taken': self.date_taken.isoformat() if self.date_taken else None,
            'photographer': self.photographer,
            'description': self.description,
            'camera_make': self.camera_make,
            'camera_model': self.camera_model,
            'exposure_time': self.exposure_time,
            'f_number': self.f_number,
            'iso_speed': self.iso_speed,
            'focal_length': self.focal_length
        }
