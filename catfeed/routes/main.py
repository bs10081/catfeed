from flask import Blueprint, render_template, session
from flask_login import current_user
from catfeed.models import CatProfile, FeedingRecord, Photo
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Get the latest cat profile
    cat = CatProfile.query.order_by(CatProfile.id.desc()).first()
    
    # Get today's feeding records
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today + timedelta(days=1), datetime.min.time())
    
    today_feedings = FeedingRecord.query.filter(
        FeedingRecord.timestamp >= today_start,
        FeedingRecord.timestamp < today_end
    ).order_by(FeedingRecord.timestamp.desc()).all()
    
    # 檢查每條記錄的編輯權限
    session_id = session.get('session_id')
    for record in today_feedings:
        record.can_edit = record.can_edit and record.session_id == session_id
    
    # Get recent photos
    recent_photos = Photo.query.filter_by(is_approved=True).order_by(
        Photo.upload_date.desc()
    ).limit(6).all()
    
    return render_template('main/index.html',
                         cat=cat,
                         today_feedings=today_feedings,
                         recent_photos=recent_photos)
