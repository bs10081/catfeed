from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from catfeed.models import FeedingRecord, CatProfile
from catfeed import db, limiter
from datetime import datetime, timedelta
import os

bp = Blueprint('feeding', __name__, url_prefix='/feeding')

@bp.route('/record', methods=['POST'])
@login_required
@limiter.limit(os.getenv('RATELIMIT_API_LIMIT', '30 per minute'))
def record():
    try:
        amount = float(request.form.get('amount'))
        calories = int(request.form.get('calories', 0))
        notes = request.form.get('notes', '')
        
        record = FeedingRecord(
            amount=amount,
            calories=calories,
            notes=notes
        )
        db.session.add(record)
        db.session.commit()
        flash('餵食記錄已新增', 'success')
    except ValueError:
        flash('請輸入有效的數值', 'danger')
    except Exception as e:
        db.session.rollback()
        flash('記錄新增失敗，請稍後再試', 'danger')
        
    return redirect(request.referrer)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    record = FeedingRecord.query.get_or_404(id)
    try:
        db.session.delete(record)
        db.session.commit()
        flash('記錄已刪除', 'success')
    except Exception as e:
        db.session.rollback()
        flash('刪除失敗，請稍後再試', 'danger')
    return redirect(url_for('feeding.history'))

@bp.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit(id):
    record = FeedingRecord.query.get_or_404(id)
    try:
        record.amount = float(request.form.get('amount'))
        record.calories = int(request.form.get('calories', 0))
        record.notes = request.form.get('notes', '')
        db.session.commit()
        flash('記錄已更新', 'success')
    except ValueError:
        flash('請輸入有效的數值', 'danger')
    except Exception as e:
        db.session.rollback()
        flash('更新失敗，請稍後再試', 'danger')
    return redirect(url_for('feeding.history'))

@bp.route('/history')
@login_required
def history():
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    records = FeedingRecord.query\
        .filter(FeedingRecord.timestamp >= start_date)\
        .order_by(FeedingRecord.timestamp.desc())\
        .all()
        
    return render_template('feeding/history.html', records=records, days=days)

@bp.route('/export')
@login_required
def export():
    import csv
    from io import StringIO
    from flask import make_response
    
    # 取得所有記錄
    records = FeedingRecord.query.order_by(FeedingRecord.timestamp.desc()).all()
    
    # 創建 CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['時間', '餵食量(g)', '熱量(kcal)', '備註'])
    
    for record in records:
        writer.writerow([
            record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            record.amount,
            record.calories or '',
            record.notes or ''
        ])
    
    # 創建回應
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=feeding_records.csv'
    
    return response

@bp.route('/api/stats')
@login_required
def stats_api():
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    records = FeedingRecord.query\
        .filter(FeedingRecord.timestamp >= start_date)\
        .order_by(FeedingRecord.timestamp.asc())\
        .all()
    
    dates = []
    amounts = []
    calories = []
    
    current_date = start_date.date()
    end_date = datetime.utcnow().date()
    
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        day_records = [r for r in records if r.timestamp.date() == current_date]
        amounts.append(sum(r.amount for r in day_records))
        calories.append(sum(r.calories or 0 for r in day_records))
        current_date += timedelta(days=1)
    
    # 計算統計資料
    if amounts:
        avg_daily_amount = sum(amounts) / len(amounts)
        avg_daily_calories = sum(calories) / len(calories)
        max_daily_amount = max(amounts)
        min_daily_amount = min(amounts)
    else:
        avg_daily_amount = avg_daily_calories = max_daily_amount = min_daily_amount = 0
    
    return jsonify({
        'dates': dates,
        'amounts': amounts,
        'calories': calories,
        'statistics': {
            'avg_daily_amount': round(avg_daily_amount, 1),
            'avg_daily_calories': round(avg_daily_calories),
            'max_daily_amount': round(max_daily_amount, 1),
            'min_daily_amount': round(min_daily_amount, 1)
        }
    })

@bp.route('/stats')
@login_required
def stats():
    days = request.args.get('days', 7, type=int)
    stats_data = stats_api().get_json()
    
    return render_template('feeding/stats.html',
                         dates=stats_data['dates'],
                         amounts=stats_data['amounts'],
                         calories=stats_data['calories'],
                         avg_daily_amount=stats_data['statistics']['avg_daily_amount'],
                         avg_daily_calories=stats_data['statistics']['avg_daily_calories'],
                         max_daily_amount=stats_data['statistics']['max_daily_amount'],
                         min_daily_amount=stats_data['statistics']['min_daily_amount'],
                         days=days)
