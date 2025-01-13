from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from catfeed.models import Admin
from catfeed import db, limiter
import os

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit(os.getenv('RATELIMIT_LOGIN_LIMIT', '5 per minute'))
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = Admin.query.filter_by(username=username).first()
        
        if user and user.is_locked_out():
            flash('帳號已被暫時鎖定，請稍後再試。', 'danger')
            return render_template('auth/login.html')
            
        if user and user.check_password(password):
            user.update_login_success()
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            if user:
                user.update_login_failure()
            flash('使用者名稱或密碼錯誤', 'danger')
            
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功登出', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
@limiter.limit(os.getenv('RATELIMIT_API_LIMIT', '30 per minute'))
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('目前密碼錯誤', 'danger')
        elif new_password != confirm_password:
            flash('新密碼與確認密碼不符', 'danger')
        elif len(new_password) < 8:
            flash('新密碼長度必須至少8個字元', 'danger')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('密碼已成功更改', 'success')
            return redirect(url_for('admin.dashboard'))
            
    return render_template('auth/change_password.html')
