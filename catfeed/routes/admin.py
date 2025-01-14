from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from catfeed.models import CatProfile, Photo, FeedingRecord
from catfeed import db, limiter
import os
from datetime import datetime

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@login_required
def dashboard():
    cat = CatProfile.query.first()
    
    # 獲取今日的餵食記錄
    today = datetime.now().date()
    records = FeedingRecord.query.filter(
        FeedingRecord.timestamp >= today
    ).order_by(FeedingRecord.timestamp.desc()).all()
    
    return render_template('admin/dashboard.html', cat=cat, records=records)

@bp.route('/update_profile', methods=['POST'])
@login_required
@limiter.limit(os.getenv('RATELIMIT_API_LIMIT', '30 per minute'))
def update_profile():
    cat = CatProfile.query.first()
    if not cat:
        cat = CatProfile()
        db.session.add(cat)
    
    cat.name = request.form.get('name')
    cat.weight = float(request.form.get('weight'))
    cat.target_weight = float(request.form.get('target_weight'))
    cat.daily_calories = int(request.form.get('daily_calories'))
    cat.meals_per_day = int(request.form.get('meals_per_day'))
    
    try:
        db.session.commit()
        flash('貓咪資料已更新', 'success')
    except Exception as e:
        db.session.rollback()
        flash('更新失敗，請稍後再試', 'danger')
        
    return redirect(url_for('admin.dashboard'))

@bp.route('/settings')
@login_required
def settings():
    return render_template('admin/settings.html')

@bp.route('/system_info')
@login_required
def system_info():
    from catfeed.models import Photo, FeedingRecord
    import os
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'catfeed.db')
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    return jsonify({
        'db_size': f'{db_size / (1024*1024):.1f} MB',
        'photo_count': Photo.query.count(),
        'record_count': FeedingRecord.query.count()
    })
