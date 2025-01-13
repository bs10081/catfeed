from flask import Blueprint, render_template
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
    today_feedings = FeedingRecord.query.filter(
        FeedingRecord.timestamp >= today
    ).order_by(FeedingRecord.timestamp.desc()).all()
    
    # Get recent photos
    recent_photos = Photo.query.filter_by(is_approved=True).order_by(
        Photo.upload_date.desc()
    ).limit(6).all()
    
    return render_template('main/index.html',
                         cat=cat,
                         today_feedings=today_feedings,
                         recent_photos=recent_photos)
