from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

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
    food_type = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), default='g')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    calories = db.Column(db.Float)

class CatProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, default=4.0)
    is_neutered = db.Column(db.Boolean, default=True)
    activity_level = db.Column(db.String(10), default='low')

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

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

@app.route('/')
def index():
    today = datetime.now().date()
    records = FeedingRecord.query.filter(
        db.func.date(FeedingRecord.timestamp) == today
    ).order_by(FeedingRecord.timestamp.desc()).all()
    
    total_calories = sum(record.calories or 0 for record in records)
    cat = CatProfile.query.first()
    daily_needs = calculate_daily_needs(cat.weight, cat.is_neutered, cat.activity_level)
    
    status = {
        'message': '',
        'type': 'info'
    }
    
    if total_calories == 0:
        status['message'] = '貓貓 肚肚 餓餓 🥺'
        status['type'] = 'warning'
    elif total_calories > daily_needs:
        status['message'] = '再吃就要胖了！🐱'
        status['type'] = 'danger'
    else:
        remaining = daily_needs - total_calories
        status['message'] = f'還可以吃 {remaining:.1f} 大卡'
        status['type'] = 'success'

    all_records = FeedingRecord.query.order_by(FeedingRecord.timestamp.desc()).all()
    return render_template('index.html', 
                         records=all_records, 
                         status=status,
                         total_calories=total_calories,
                         daily_needs=daily_needs)

@app.route('/add_record', methods=['POST'])
def add_record():
    food_type = request.form.get('food_type')
    amount = float(request.form.get('amount'))
    notes = request.form.get('notes')
    
    calories = calculate_calories(food_type, amount)
    
    new_record = FeedingRecord(
        food_type=food_type,
        amount=amount,
        notes=notes,
        calories=calories
    )
    
    db.session.add(new_record)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Admin.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('帳號或密碼錯誤')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    cat = CatProfile.query.first()
    return render_template('admin_dashboard.html', cat=cat)

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

if __name__ == '__main__':
    app.run(debug=True)
