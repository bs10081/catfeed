from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import pytz
from dotenv import load_dotenv
import json
from auth.limiter import init_limiter, rate_limit_by_ip, rate_limit_by_user, block_ip, is_ip_blocked

# 載入環境變數
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/catfeed.db')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("No SECRET_KEY set for Flask application. Please set FLASK_SECRET_KEY in .env file")
    
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

# Redis 配置
app.config['REDIS_ENABLED'] = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
app.config['REDIS_HOST'] = os.getenv('REDIS_HOST', 'localhost')
app.config['REDIS_PORT'] = int(os.getenv('REDIS_PORT', 6379))
app.config['REDIS_DB'] = int(os.getenv('REDIS_DB', 0))

# 速率限制配置
app.config['RATELIMIT_DEFAULT'] = os.getenv('RATELIMIT_DEFAULT', '200 per day')
app.config['RATELIMIT_LOGIN_LIMIT'] = os.getenv('RATELIMIT_LOGIN_LIMIT', '5 per minute')
app.config['RATELIMIT_SIGNUP_LIMIT'] = os.getenv('RATELIMIT_SIGNUP_LIMIT', '2 per hour')
app.config['RATELIMIT_API_LIMIT'] = os.getenv('RATELIMIT_API_LIMIT', '30 per minute')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 確保上傳目錄存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# 初始化速率限制器
limiter = init_limiter(app)

# 錯誤處理
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error": "請求過於頻繁，請稍後再試",
        "description": str(e.description)
    }), 429

# 修改速率限制的鍵生成函數
def get_rate_limit_key():
    if current_user.is_authenticated:
        # 已登入用戶使用用戶ID作為限制鍵
        return str(current_user.id)
    # 未登入用戶使用IP
    return request.remote_addr

# 配置limiter使用自定義的鍵生成函數
limiter.key_func = get_rate_limit_key

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    last_password_change = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    password_history = db.Column(db.JSON, default=list)  # 存儲最近的密碼哈希
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    account_locked_until = db.Column(db.DateTime)
    force_password_change = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        from auth import PasswordValidator, PasswordPolicy
        
        # 驗證新密碼
        validator = PasswordValidator()
        is_valid, error_msg = validator.validate(password, [self.username])
        if not is_valid:
            raise ValueError(error_msg)
            
        # 檢查密碼歷史
        policy = PasswordPolicy()
        new_hash = generate_password_hash(password)
        if not policy.can_reuse_password(new_hash, self.password_history or []):
            raise ValueError("不能重複使用最近使用過的密碼")
            
        # 更新密碼
        self.password_hash = new_hash
        self.last_password_change = datetime.utcnow()
        
        # 更新密碼歷史
        history = self.password_history or []
        history.append(new_hash)
        if len(history) > policy.history_size:
            history = history[-policy.history_size:]
        self.password_history = history
        
        self.force_password_change = False
        self.failed_login_attempts = 0
        self.account_locked_until = None

    def check_password(self, password):
        # 檢查帳戶是否被鎖定
        if self.account_locked_until and self.account_locked_until > datetime.utcnow():
            raise ValueError(f"帳戶已被鎖定，請在 {self.account_locked_until} 後重試")
            
        is_valid = check_password_hash(self.password_hash, password)
        
        if not is_valid:
            self.failed_login_attempts += 1
            self.last_failed_login = datetime.utcnow()
            
            # 如果失敗次數過多，鎖定帳戶
            if self.failed_login_attempts >= 5:
                lock_duration = timedelta(minutes=15)  # 15分鐘後解鎖
                self.account_locked_until = datetime.utcnow() + lock_duration
                db.session.commit()
                raise ValueError(f"登入失敗次數過多，帳戶已被鎖定 {lock_duration.seconds//60} 分鐘")
            
            db.session.commit()
            return False
            
        # 登入成功，重置失敗計數
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.last_failed_login = None
            self.account_locked_until = None
            db.session.commit()
            
        # 檢查密碼是否過期
        from auth import PasswordPolicy
        policy = PasswordPolicy()
        if policy.is_password_expired(self.last_password_change):
            self.force_password_change = True
            db.session.commit()
            
        return True

    def needs_password_change(self):
        """檢查是否需要更改密碼"""
        return self.force_password_change or (
            self.last_password_change and 
            PasswordPolicy().is_password_expired(self.last_password_change)
        )

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

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    date_taken = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    photographer = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)

class Biography(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    
    if is_neutered:
        multiplier = {
            'low': 1.2,
            'normal': 1.4,
            'high': 1.6
        }.get(activity_level, 1.4)
    else:
        multiplier = {
            'low': 1.4,
            'normal': 1.6,
            'high': 1.8
        }.get(activity_level, 1.6)
    
    return rer * multiplier

def calculate_remaining_treats(total_calories, daily_needs):
    # 如果今天還沒吃東西
    if total_calories == 0:
        return '貓貓 肚肚 餓餓 🥺'
    # 如果已經超過每日建議量
    elif total_calories > daily_needs:
        return '再吃就要胖了！🐱'
    # 如果還在建議量內
    else:
        remaining = daily_needs - total_calories
        return f'還可以吃 {remaining:.1f} 大卡'

def can_edit_record(record):
    """檢查記錄是否在可編輯時間範圍內（15分鐘）"""
    if not record:
        return False
    now = datetime.utcnow()
    time_diff = now - record.timestamp
    return time_diff.total_seconds() <= 900  # 15分鐘 = 900秒

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        admin.set_password('catfeed2024@TW')  # 設定更強的默認密碼
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    # 獲取當前時區
    local_tz = get_current_timezone()
    now = datetime.now(local_tz)

    # 獲取貓咪資料
    cat = CatProfile.query.first()
    if not cat:
        cat = CatProfile()
        db.session.add(cat)
        db.session.commit()

    # 計算今日攝取的卡路里
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    records = FeedingRecord.query.filter(
        FeedingRecord.timestamp >= today_start.astimezone(pytz.UTC)
    ).order_by(FeedingRecord.timestamp.desc()).all()

    # 轉換時間到本地時區
    for record in records:
        record.local_time = convert_to_local_time(record.timestamp)

    # 計算今日總卡路里
    total_calories = sum(record.calories for record in records if record.calories)

    # 計算每日建議攝取量
    daily_needs = calculate_daily_needs(cat.weight, cat.is_neutered, cat.activity_level)

    # 計算剩餘零食量
    remaining_treats = calculate_remaining_treats(total_calories, daily_needs)

    # 檢查是否有狀態消息
    status = {}
    if 'status_type' in request.args and 'status_message' in request.args:
        status = {
            'type': request.args.get('status_type'),
            'message': request.args.get('status_message')
        }

    all_records = FeedingRecord.query.order_by(FeedingRecord.timestamp.desc()).all()
    for record in all_records:
        record.local_time = convert_to_local_time(record.timestamp)

    treats_message = f'今日還可以吃 {max(2 - sum(1 for record in records if record.food_type == "貓條"), 0)} 條貓條'

    # 獲取最近的照片（最多5張）
    recent_photos = Photo.query.filter_by(is_approved=True).order_by(Photo.date_taken.desc()).limit(5).all()

    return render_template('index.html',
                         records=all_records,
                         total_calories=total_calories,
                         daily_needs=daily_needs,
                         remaining_treats=remaining_treats,
                         status=status,
                         now=now,
                         can_edit_record=can_edit_record,
                         recent_photos=recent_photos)

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

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit(os.getenv('RATELIMIT_LOGIN_LIMIT', '5 per minute'))
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if not admin:
            flash('使用者名稱或密碼錯誤', 'error')
            return redirect(url_for('admin_login'))
            
        try:
            if admin.check_password(password):
                login_user(admin)
                
                # 如果需要更改密碼，重定向到密碼更改頁面
                if admin.needs_password_change():
                    flash('您的密碼已過期，請更改密碼', 'warning')
                    return redirect(url_for('change_password'))
                    
                return redirect(url_for('admin_dashboard'))
            else:
                flash('使用者名稱或密碼錯誤', 'error')
                # 如果登入失敗次數過多，封鎖 IP
                if admin.failed_login_attempts >= 5:
                    block_ip(request.remote_addr, 900)  # 封鎖 15 分鐘
        except ValueError as e:
            flash(str(e), 'error')
            
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

@app.route('/admin/change_password', methods=['GET', 'POST'])
@login_required
@limiter.limit(os.getenv('RATELIMIT_API_LIMIT', '30 per minute'))
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('當前密碼錯誤', 'error')
            return redirect(url_for('change_password'))
            
        if new_password != confirm_password:
            flash('新密碼與確認密碼不符', 'error')
            return redirect(url_for('change_password'))
            
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('密碼已更新', 'success')
            
            # 如果是強制更改密碼，更新後重定向到儀表板
            if current_user.force_password_change:
                return redirect(url_for('admin_dashboard'))
                
            return redirect(url_for('admin_dashboard'))
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('change_password'))
            
    return render_template('change_password.html', force_change=current_user.force_password_change)

@app.route('/admin/update_profile', methods=['POST'])
@login_required
@limiter.limit(os.getenv('RATELIMIT_API_LIMIT', '30 per minute'))
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

# 關於頁面路由
@app.route('/about')
def about():
    approved_photos = Photo.query.filter_by(is_approved=True).order_by(Photo.date_taken.desc()).all()
    biographies = Biography.query.order_by(Biography.date.desc()).all()
    return render_template('about.html', photos=approved_photos, biographies=biographies)

# 照片上傳路由
@app.route('/upload_photo', methods=['POST'])
@limiter.limit(os.getenv('RATELIMIT_API_LIMIT', '30 per minute'))
def upload_photo():
    if 'photo' not in request.files:
        flash('未選擇檔案', 'danger')
        return redirect(url_for('about'))
    
    file = request.files['photo']
    if file.filename == '':
        flash('未選擇檔案', 'danger')
        return redirect(url_for('about'))

    if not allowed_file(file.filename):
        flash('不支援的檔案格式', 'danger')
        return redirect(url_for('about'))

    try:
        date_taken = datetime.strptime(request.form['date_taken'], '%Y-%m-%d')
    except ValueError:
        flash('無效的日期格式', 'danger')
        return redirect(url_for('about'))

    if not request.form.get('photographer'):
        flash('請填寫拍攝者', 'danger')
        return redirect(url_for('about'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 使用時間戳確保檔名唯一
        unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        
        new_photo = Photo(
            filename=unique_filename,
            original_filename=filename,
            date_taken=date_taken,
            description=request.form.get('description', ''),
            photographer=request.form['photographer'],
            is_approved=False  # 確保新上傳的照片預設為未審核狀態
        )
        db.session.add(new_photo)
        db.session.commit()
        
        flash('照片上傳成功，等待管理員審核', 'success')
        return redirect(url_for('about'))

# 照片審核路由
@app.route('/admin/photos')
@login_required
@limiter.limit(os.getenv('RATELIMIT_API_LIMIT', '30 per minute'))
def admin_photos():
    pending_photos = Photo.query.filter_by(is_approved=False).order_by(Photo.upload_date.desc()).all()
    approved_photos = Photo.query.filter_by(is_approved=True).order_by(Photo.upload_date.desc()).all()
    return render_template('admin_photos.html', pending_photos=pending_photos, approved_photos=approved_photos)

# 審核照片路由
@app.route('/admin/approve_photo/<int:photo_id>', methods=['POST'])
@login_required
def approve_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo.is_approved = True
    db.session.commit()
    flash('照片已審核通過', 'success')
    return redirect(url_for('admin_photos'))

# 刪除照片路由
@app.route('/admin/delete_photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], photo.filename))
    except OSError:
        pass  # 如果檔案不存在就忽略
    db.session.delete(photo)
    db.session.commit()
    flash('照片已刪除', 'success')
    return redirect(url_for('admin_photos'))

# 提供照片檔案的路由
@app.route('/uploads/<filename>')
@limiter.limit(os.getenv('RATELIMIT_DEFAULT', '200 per day'), exempt_when=lambda: current_user.is_authenticated)
def uploaded_file(filename):
    try:
        response = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 一年的快取
        response.headers['X-Accel-Buffering'] = 'no'  # 禁用 Nginx 緩衝
        return response
    except FileNotFoundError:
        return "照片不存在", 404
    except Exception as e:
        app.logger.error(f"讀取照片時發生錯誤: {str(e)}")
        return "讀取照片時發生錯誤", 500

# 生平記事路由
@app.route('/admin/biography', methods=['GET', 'POST'])
@login_required
def manage_biography():
    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            if not date_str:
                flash('日期為必填項目', 'danger')
                return redirect(url_for('manage_biography'))
            
            date = datetime.strptime(date_str, '%Y-%m-%d')
            content = request.form.get('content')
            
            if not content:
                flash('內容為必填項目', 'danger')
                return redirect(url_for('manage_biography'))
            
            bio_id = request.form.get('bio_id', type=int)
            if bio_id:  # 更新現有記事
                bio = Biography.query.get_or_404(bio_id)
                bio.date = date
                bio.content = content
                flash('生平記事已更新', 'success')
            else:  # 新增記事
                bio = Biography(date=date, content=content)
                db.session.add(bio)
                flash('生平記事已新增', 'success')
            
            db.session.commit()
            return redirect(url_for('manage_biography'))
        except ValueError:
            flash('無效的日期格式', 'danger')
            return redirect(url_for('manage_biography'))
    
    biographies = Biography.query.order_by(Biography.date.desc()).all()
    return render_template('admin_biography.html', biographies=biographies)

@app.route('/api/biography')
def get_biography():
    biographies = Biography.query.order_by(Biography.date.desc()).all()
    return jsonify([{
        'id': bio.id,
        'date': bio.date.strftime('%Y-%m-%d'),
        'content': bio.content
    } for bio in biographies])

@app.route('/admin/biography/<int:bio_id>', methods=['DELETE'])
@login_required
def delete_biography(bio_id):
    bio = Biography.query.get_or_404(bio_id)
    db.session.delete(bio)
    db.session.commit()
    flash('生平記事已刪除', 'success')
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
