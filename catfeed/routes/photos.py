from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from catfeed.models import Photo
from catfeed import db, limiter
import os
import uuid
from datetime import datetime

bp = Blueprint('photos', __name__, url_prefix='/photos')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def process_image(file_path, max_size=(800, 800)):
    from PIL import Image, ExifTags
    from io import BytesIO
    
    try:
        with Image.open(file_path) as img:
            # 讀取 EXIF 資料
            exif_data = {}
            if hasattr(img, '_getexif') and img._getexif():
                for tag_id, value in img._getexif().items():
                    if tag_id in ExifTags.TAGS:
                        exif_data[ExifTags.TAGS[tag_id]] = str(value)
            
            # 修正圖片方向
            if 'Orientation' in exif_data:
                orientation = int(exif_data['Orientation'])
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
            
            # 調整圖片大小
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 儲存壓縮後的圖片
            output = BytesIO()
            img.save(output, format=img.format, quality=85, optimize=True)
            with open(file_path, 'wb') as f:
                f.write(output.getvalue())
            
            return exif_data
    except Exception as e:
        current_app.logger.error(f"處理圖片時發生錯誤: {str(e)}")
        return None

@bp.route('/upload', methods=['POST'])
@login_required
@limiter.limit(os.getenv('RATELIMIT_API_LIMIT', '30 per minute'))
def upload():
    if 'photo' not in request.files:
        flash('未選擇檔案', 'danger')
        return redirect(request.referrer)
        
    file = request.files['photo']
    if file.filename == '':
        flash('未選擇檔案', 'danger')
        return redirect(request.referrer)
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            file.save(file_path)
            
            # 處理圖片
            exif_data = process_image(file_path)
            
            photo = Photo(
                filename=unique_filename,
                original_filename=filename,
                file_size=os.path.getsize(file_path),
                mime_type=file.content_type,
                exif_data=exif_data
            )
            db.session.add(photo)
            db.session.commit()
            flash('照片上傳成功', 'success')
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.rollback()
            flash('照片上傳失敗，請稍後再試', 'danger')
    else:
        flash('不支援的檔案格式', 'danger')
        
    return redirect(request.referrer)

@bp.route('/manage')
@login_required
def manage():
    photos = Photo.query.order_by(Photo.upload_date.desc()).all()
    return render_template('photos/manage.html', photos=photos)

@bp.route('/approve/<int:id>', methods=['POST'])
@login_required
def approve(id):
    photo = Photo.query.get_or_404(id)
    photo.is_approved = True
    db.session.commit()
    flash('照片已核准', 'success')
    return redirect(url_for('photos.manage'))

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    photo = Photo.query.get_or_404(id)
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        db.session.delete(photo)
        db.session.commit()
        flash('照片已刪除', 'success')
    except Exception as e:
        db.session.rollback()
        flash('刪除失敗，請稍後再試', 'danger')
    return redirect(url_for('photos.manage'))

@bp.route('/view/<filename>')
@limiter.limit(os.getenv('RATELIMIT_DEFAULT', '200 per day'), 
               exempt_when=lambda: current_user.is_authenticated)
def view(filename):
    try:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return "照片不存在", 404
