from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catfeed.db'
app.config['SECRET_KEY'] = os.urandom(24)  # 用於session加密
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FeedingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    food_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), default='克')
    calories = db.Column(db.Float)
    notes = db.Column(db.Text)
    feeder_nickname = db.Column(db.String(50), nullable=False)  # 新增餵食人暱稱欄位

    def __repr__(self):
        return f'<FeedingRecord {self.timestamp} {self.food_type}>'

class CatProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, default=4.0)
    is_neutered = db.Column(db.Boolean, default=True)
    activity_level = db.Column(db.String(10), default='low')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timezone = db.Column(db.String(50), default='Asia/Taipei')

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

def get_current_timezone():
    settings = Settings.query.first()
    return pytz.timezone(settings.timezone if settings else 'Asia/Taipei')

def convert_to_local_time(utc_dt):
    if not utc_dt:
        return None
    local_tz = get_current_timezone()
    return pytz.utc.localize(utc_dt).astimezone(local_tz)

def calculate_calories(food_type, amount):
    calories_per_gram = {
        '貓罐頭': 0.8,
        '貓條': 5,
        '乾糧': 3.5,
        '其他': 1.0
    }
    return amount * calories_per_gram.get(food_type, 1.0)

def calculate_daily_needs(weight, is_neutered, activity_level):
    rer = 70 * (weight ** 0.75)
    activity_factor = 1.2 if activity_level == 'low' else 1.4
    if not is_neutered:
        activity_factor += 0.1
    der = rer * activity_factor
    return der

def can_edit_record(record):
    """檢查記錄是否在可編輯時間範圍內（15分鐘）"""
    if not record:
        return False
    now = datetime.utcnow()
    time_diff = now - record.timestamp
    return time_diff.total_seconds() <= 900  # 15分鐘 = 900秒

with app.app_context():
    db.create_all()
    # 確保有一個貓咪檔案
    if not CatProfile.query.first():
        default_profile = CatProfile()
        db.session.add(default_profile)
        db.session.commit()
    # 創建默認管理員帳號（如果不存在）
    if not Admin.query.first():
        admin = Admin(username='admin')
        admin.set_password('catfeed2024')  # 設定默認密碼
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    local_tz = get_current_timezone()
    today = datetime.now(local_tz).date()
    now = datetime.utcnow()
    
    records = FeedingRecord.query.filter(
        db.func.date(FeedingRecord.timestamp) == today
    ).order_by(FeedingRecord.timestamp.desc()).all()
    
    # 轉換記錄時間到本地時區
    for record in records:
        record.local_time = convert_to_local_time(record.timestamp)
    
    total_calories = sum(record.calories or 0 for record in records)
    treats_today = sum(1 for record in records if record.food_type == '貓條')
    remaining_treats = max(2 - treats_today, 0)
    
    cat = CatProfile.query.first()
    daily_needs = calculate_daily_needs(cat.weight, cat.is_neutered, cat.activity_level)
    
    status = {
        'message': '',
        'type': 'info'
    }
    
    if total_calories == 0:
        status['message'] = f'貓貓 肚肚 餓餓 🥺'
        status['type'] = 'warning'
    elif total_calories > daily_needs:
        status['message'] = f'再吃就要胖了！🐱'
        status['type'] = 'danger'
    else:
        remaining = daily_needs - total_calories
        status['message'] = f'還可以吃 {remaining:.1f} 大卡'
        status['type'] = 'success'

    all_records = FeedingRecord.query.order_by(FeedingRecord.timestamp.desc()).all()
    for record in all_records:
        record.local_time = convert_to_local_time(record.timestamp)
    
    treats_message = f'今日還可以吃 {remaining_treats} 條貓條'
    
    return render_template('index.html', 
                         records=all_records, 
                         status=status,
                         total_calories=total_calories,
                         daily_needs=daily_needs,
                         remaining_treats=treats_message,
                         now=now,
                         can_edit_record=can_edit_record)

@app.route('/add_record', methods=['POST'])
def add_record():
    food_type = request.form.get('food_type')
    amount = float(request.form.get('amount'))
    notes = request.form.get('notes')
    feeder_nickname = request.form.get('feeder_nickname')
    
    calories = calculate_calories(food_type, amount)
    
    new_record = FeedingRecord(
        food_type=food_type,
        amount=amount,
        notes=notes,
        calories=calories,
        feeder_nickname=feeder_nickname
    )
    
    db.session.add(new_record)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Admin.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('登入成功', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('帳號或密碼錯誤', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    timezones = pytz.common_timezones
    current_timezone = get_current_timezone()
    records = FeedingRecord.query.order_by(FeedingRecord.timestamp.desc()).all()
    for record in records:
        record.local_time = convert_to_local_time(record.timestamp)
    
    # 獲取貓咪資料和設定
    cat = CatProfile.query.first()
    if not cat:
        cat = CatProfile(name='滅霸', weight=4.5, daily_calories=237.6)
        db.session.add(cat)
        db.session.commit()
    
    settings = Settings.query.first()
    if not settings:
        settings = Settings(timezone='Asia/Taipei')
        db.session.add(settings)
        db.session.commit()
    
    return render_template('admin_dashboard.html', 
                         timezones=timezones, 
                         current_timezone=current_timezone,
                         records=records,
                         cat=cat,
                         settings=settings)

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # 驗證當前密碼
    if not current_user.check_password(current_password):
        flash('目前密碼不正確', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # 驗證新密碼
    if new_password != confirm_password:
        flash('新密碼與確認密碼不符', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if len(new_password) < 6:
        flash('新密碼長度必須至少6個字元', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # 更新密碼
    current_user.set_password(new_password)
    db.session.commit()
    flash('密碼已成功更新', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_profile', methods=['POST'])
@login_required
def update_profile():
    cat = CatProfile.query.first()
    cat.weight = float(request.form.get('weight'))
    cat.is_neutered = request.form.get('is_neutered') == 'true'
    cat.activity_level = request.form.get('activity_level')
    
    db.session.commit()
    flash('貓咪資料已更新')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_timezone', methods=['POST'])
@login_required
def update_timezone():
    timezone = request.form.get('timezone')
    if timezone not in pytz.common_timezones:
        flash('無效的時區設定', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    settings = Settings.query.first()
    if not settings:
        settings = Settings(timezone=timezone)
        db.session.add(settings)
    else:
        settings.timezone = timezone
    
    db.session.commit()
    flash('時區設定已更新', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_record/<int:record_id>', methods=['GET', 'POST'])
def edit_record(record_id):
    record = FeedingRecord.query.get_or_404(record_id)
    
    if not can_edit_record(record):
        flash('超過編輯時間限制（15分鐘）', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        record.food_type = request.form.get('food_type')
        record.amount = float(request.form.get('amount'))
        record.notes = request.form.get('notes')
        record.feeder_nickname = request.form.get('feeder_nickname')
        record.calories = calculate_calories(record.food_type, record.amount)
        
        db.session.commit()
        flash('記錄已更新', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit_record.html', record=record)

@app.route('/delete_record/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    record = FeedingRecord.query.get_or_404(record_id)
    
    if not can_edit_record(record):
        flash('超過編輯時間限制（15分鐘）', 'warning')
        return redirect(url_for('index'))
    
    db.session.delete(record)
    db.session.commit()
    flash('記錄已刪除', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
