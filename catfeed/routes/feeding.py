from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from catfeed.models import FeedingRecord, CatProfile
from catfeed import db, limiter
from datetime import datetime, timedelta
import os

bp = Blueprint('feeding', __name__, url_prefix='/feeding')

@bp.route('/record', methods=['POST'])
@limiter.limit(os.getenv('RATELIMIT_API_LIMIT', '30 per minute'))
def record():
    try:
        amount = float(request.form.get('amount'))
        calories = int(request.form.get('calories', 0))
        notes = request.form.get('notes', '')
        
        # 如果是管理員，直接核准記錄
        is_approved = current_user.is_authenticated
        
        record = FeedingRecord(
            amount=amount,
            calories=calories,
            notes=notes,
            is_approved=is_approved
        )
        db.session.add(record)
        db.session.commit()
        flash('餵食記錄已新增' + (' 並已自動核准' if is_approved else '，等待管理員審核'), 'success')
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
        amount = float(request.form.get('amount'))
        calories = int(request.form.get('calories', 0))
        notes = request.form.get('notes', '')
        
        record.amount = amount
        record.calories = calories
        record.notes = notes
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
    days = request.args.get('days', default=7, type=int)
    since = datetime.now() - timedelta(days=days)
    records = FeedingRecord.query.filter(FeedingRecord.timestamp >= since)\
        .order_by(FeedingRecord.timestamp.desc()).all()
    return render_template('feeding/history.html', records=records, days=days)

@bp.route('/export')
@login_required
def export():
    try:
        days = request.args.get('days', default=30, type=int)
        since = datetime.now() - timedelta(days=days)
        records = FeedingRecord.query.filter(FeedingRecord.timestamp >= since)\
            .order_by(FeedingRecord.timestamp.desc()).all()
        
        import csv
        from io import StringIO
        import tempfile
        
        # 創建暫存檔案
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow(['時間', '數量', '卡路里', '備註'])
            
            for record in records:
                writer.writerow([
                    record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    record.amount,
                    record.calories,
                    record.notes
                ])
            
            temp_file_path = temp_file.name
        
        from flask import send_file
        return send_file(
            temp_file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'feeding_records_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        flash('匯出失敗，請稍後再試', 'danger')
        return redirect(url_for('feeding.history'))

@bp.route('/api/stats')
@limiter.limit(os.getenv('RATELIMIT_DEFAULT', '200 per day'),
               exempt_when=lambda: current_user.is_authenticated)
def stats_api():
    try:
        days = request.args.get('days', default=7, type=int)
        since = datetime.now() - timedelta(days=days)
        records = FeedingRecord.query.filter(
            FeedingRecord.timestamp >= since,
            FeedingRecord.is_approved == True
        ).order_by(FeedingRecord.timestamp.asc()).all()
        
        # 計算每日統計
        daily_stats = {}
        for record in records:
            date = record.timestamp.date()
            if date not in daily_stats:
                daily_stats[date] = {
                    'total_amount': 0,
                    'total_calories': 0,
                    'count': 0
                }
            daily_stats[date]['total_amount'] += record.amount
            daily_stats[date]['total_calories'] += record.calories
            daily_stats[date]['count'] += 1
        
        # 轉換成列表格式
        stats_list = []
        current = since.date()
        end = datetime.now().date()
        while current <= end:
            stats = daily_stats.get(current, {
                'total_amount': 0,
                'total_calories': 0,
                'count': 0
            })
            stats_list.append({
                'date': current.strftime('%Y-%m-%d'),
                'total_amount': stats['total_amount'],
                'total_calories': stats['total_calories'],
                'count': stats['count']
            })
            current += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'data': stats_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@bp.route('/stats')
def stats():
    days = request.args.get('days', default=7, type=int)
    cats = CatProfile.query.all()
    return render_template('feeding/stats.html', days=days, cats=cats)
