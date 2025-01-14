from flask import Blueprint, request, jsonify, current_app, session
from catfeed.models import FeedingRecord, CatProfile
from catfeed import db
from datetime import datetime, timedelta
import uuid

bp = Blueprint('feeding', __name__, url_prefix='/feeding')

def get_or_create_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

@bp.route('/add', methods=['POST'])
def add_feeding():
    """添加餵食記錄"""
    try:
        current_app.logger.info('收到添加餵食記錄請求')
        current_app.logger.debug(f'請求數據: {request.get_json()}')
        
        if not request.is_json:
            return jsonify({'error': '請求必須是 JSON 格式'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': '無效的請求數據'}), 400
            
        # 驗證必要字段
        required_fields = ['food_type', 'amount']
        if not all(field in data for field in required_fields):
            missing_fields = [field for field in required_fields if field not in data]
            return jsonify({'error': f'缺少必要字段: {", ".join(missing_fields)}'}), 400
            
        # 驗證數據類型
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': '餵食量必須大於0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': '餵食量必須是有效的數字'}), 400
            
        # 獲取或創建 session_id
        session_id = get_or_create_session_id()
        
        # 獲取貓咪資料
        cat = CatProfile.query.first()
        if not cat:
            return jsonify({'error': '找不到貓咪資料'}), 404
            
        # 創建新記錄
        record = FeedingRecord(
            feeder_nickname=data.get('feeder_nickname', '訪客'),
            food_type=data['food_type'],
            amount=amount,
            calories=data.get('calories'),
            notes=data.get('notes'),
            session_id=session_id
        )
        
        db.session.add(record)
        db.session.commit()
        
        current_app.logger.info(f'成功添加餵食記錄: {record.to_dict()}')
        return jsonify({
            'message': '記錄添加成功',
            'record': record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'添加記錄時發生錯誤: {str(e)}')
        return jsonify({'error': str(e)}), 500

@bp.route('/edit/<int:record_id>', methods=['PUT'])
def edit_feeding(record_id):
    """編輯餵食記錄"""
    try:
        record = FeedingRecord.query.get_or_404(record_id)
        
        # 檢查是否可以編輯
        if not record.can_edit:
            return jsonify({'error': '記錄已超過15分鐘，無法編輯'}), 403
            
        # 檢查 session_id
        if record.session_id != get_or_create_session_id():
            return jsonify({'error': '您沒有權限編輯此記錄'}), 403
            
        if not request.is_json:
            return jsonify({'error': '請求必須是 JSON 格式'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': '無效的請求數據'}), 400
            
        # 更新記錄
        if 'food_type' in data:
            record.food_type = data['food_type']
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    return jsonify({'error': '餵食量必須大於0'}), 400
                record.amount = amount
            except (ValueError, TypeError):
                return jsonify({'error': '餵食量必須是有效的數字'}), 400
        if 'calories' in data:
            record.calories = data['calories']
        if 'notes' in data:
            record.notes = data['notes']
            
        db.session.commit()
        
        current_app.logger.info(f'成功更新餵食記錄: {record.to_dict()}')
        return jsonify({
            'message': '記錄更新成功',
            'record': record.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'編輯記錄時發生錯誤: {str(e)}')
        return jsonify({'error': str(e)}), 500

@bp.route('/delete/<int:record_id>', methods=['DELETE'])
def delete_feeding(record_id):
    """刪除餵食記錄"""
    try:
        record = FeedingRecord.query.get_or_404(record_id)
        
        # 檢查是否可以刪除
        if not record.can_edit:
            return jsonify({'error': '記錄已超過15分鐘，無法刪除'}), 403
            
        # 檢查 session_id
        if record.session_id != get_or_create_session_id():
            return jsonify({'error': '您沒有權限刪除此記錄'}), 403
            
        db.session.delete(record)
        db.session.commit()
        
        current_app.logger.info(f'成功刪除餵食記錄: {record_id}')
        return jsonify({'message': '記錄刪除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'刪除記錄時發生錯誤: {str(e)}')
        return jsonify({'error': str(e)}), 500

@bp.route('/today', methods=['GET'])
def get_today_feedings():
    try:
        today = datetime.utcnow().date()
        records = FeedingRecord.query.filter(
            db.func.date(FeedingRecord.timestamp) == today
        ).order_by(FeedingRecord.timestamp.desc()).all()
        
        return jsonify({
            'records': [record.to_dict() for record in records]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"獲取今日餵食記錄時發生錯誤: {str(e)}")
        return jsonify({'error': '獲取記錄時發生錯誤'}), 500

@bp.route('/stats')
def stats():
    try:
        # 獲取天數參數，預設為7天
        days = request.args.get('days', 7, type=int)
        if days not in [7, 30, 90]:
            days = 7
        
        # 獲取指定天數的記錄
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        records = FeedingRecord.query.filter(
            FeedingRecord.timestamp.between(start_date, end_date)
        ).order_by(FeedingRecord.timestamp.desc()).all()
        
        # 按日期分組
        daily_stats = {}
        for record in records:
            date = record.timestamp.date()
            if date not in daily_stats:
                daily_stats[date] = {
                    'total_amount': 0,
                    'total_calories': 0,
                    'feedings_count': 0,
                    'food_types': {}
                }
            
            stats = daily_stats[date]
            stats['total_amount'] += record.amount
            if record.calories:
                stats['total_calories'] += record.calories
            stats['feedings_count'] += 1
            
            # 統計食物類型
            food_type = record.food_type
            if food_type not in stats['food_types']:
                stats['food_types'][food_type] = 0
            stats['food_types'][food_type] += 1
        
        # 計算統計數據
        if daily_stats:
            dates = []
            amounts = []
            calories = []
            total_amount = 0
            total_calories = 0
            max_daily_amount = float('-inf')
            min_daily_amount = float('inf')
            
            for date in sorted(daily_stats.keys()):
                stats = daily_stats[date]
                dates.append(date.strftime('%Y-%m-%d'))
                amounts.append(stats['total_amount'])
                calories.append(stats['total_calories'])
                
                total_amount += stats['total_amount']
                total_calories += stats['total_calories']
                max_daily_amount = max(max_daily_amount, stats['total_amount'])
                min_daily_amount = min(min_daily_amount, stats['total_amount'])
            
            avg_daily_amount = total_amount / len(daily_stats)
            avg_daily_calories = total_calories / len(daily_stats)
        else:
            dates = []
            amounts = []
            calories = []
            avg_daily_amount = 0
            avg_daily_calories = 0
            max_daily_amount = 0
            min_daily_amount = 0
        
        return render_template('feeding/stats.html',
                             days=days,
                             dates=dates,
                             amounts=amounts,
                             calories=calories,
                             avg_daily_amount=avg_daily_amount,
                             avg_daily_calories=avg_daily_calories,
                             max_daily_amount=max_daily_amount,
                             min_daily_amount=min_daily_amount)
        
    except Exception as e:
        current_app.logger.error(f"獲取餵食統計時發生錯誤: {str(e)}")
        return render_template('error.html', error='獲取統計時發生錯誤'), 500
