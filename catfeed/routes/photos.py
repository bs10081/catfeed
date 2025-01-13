from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from catfeed.models import Photo
from catfeed import db, limiter
import os
import uuid
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

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

def extract_exif_data(image_path):
    """從圖片中提取 EXIF 資訊"""
    try:
        with Image.open(image_path) as img:
            if not hasattr(img, '_getexif') or img._getexif() is None:
                return {}
                
            exif = {
                TAGS.get(tag_id, tag_id): value
                for tag_id, value in img._getexif().items()
                if TAGS.get(tag_id, tag_id)
            }
            
            # 提取需要的 EXIF 資訊
            result = {}
            
            # 拍攝日期
            if 'DateTimeOriginal' in exif:
                try:
                    result['date_taken'] = datetime.strptime(exif['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
                except (ValueError, TypeError):
                    pass
            
            # 相機資訊
            if 'Make' in exif:
                result['camera_make'] = str(exif['Make']).strip()
            if 'Model' in exif:
                result['camera_model'] = str(exif['Model']).strip()
                
            # 拍攝參數
            if 'ExposureTime' in exif:
                if isinstance(exif['ExposureTime'], tuple):
                    result['exposure_time'] = f"{exif['ExposureTime'][0]}/{exif['ExposureTime'][1]}"
                else:
                    result['exposure_time'] = str(exif['ExposureTime'])
            
            if 'FNumber' in exif:
                if isinstance(exif['FNumber'], tuple):
                    result['f_number'] = float(exif['FNumber'][0]) / float(exif['FNumber'][1])
                else:
                    result['f_number'] = float(exif['FNumber'])
            
            if 'ISOSpeedRatings' in exif:
                result['iso_speed'] = int(exif['ISOSpeedRatings'])
            
            if 'FocalLength' in exif:
                if isinstance(exif['FocalLength'], tuple):
                    result['focal_length'] = float(exif['FocalLength'][0]) / float(exif['FocalLength'][1])
                else:
                    result['focal_length'] = float(exif['FocalLength'])
            
            return result
    except Exception as e:
        current_app.logger.error(f"提取 EXIF 資訊時發生錯誤: {str(e)}")
        return {}

@bp.route('/upload', methods=['POST'])
@login_required
def upload():
    try:
        if 'photo' not in request.files:
            return jsonify({'error': '沒有上傳檔案'}), 400
            
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': '沒有選擇檔案'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': '不支援的檔案格式'}), 400
            
        # 保存原始檔案名稱
        original_filename = secure_filename(file.filename)
        
        # 生成新的檔案名稱，格式：YYYYMMDD_HHMMSS_原始檔名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{original_filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # 先保存檔案以便處理
        file.save(file_path)
        
        # 處理圖片方向並調整大小
        try:
            process_image(file_path)
        except Exception as e:
            current_app.logger.error(f"處理圖片時發生錯誤: {str(e)}")
            
        # 提取 EXIF 資訊
        exif_data = extract_exif_data(file_path)
        
        # 創建照片記錄
        photo = Photo(
            filename=filename,
            original_filename=original_filename,
            file_size=os.path.getsize(file_path),
            mime_type=file.content_type,
            is_approved=current_user.is_admin,  # 管理員上傳的照片自動核准
            **exif_data  # 加入 EXIF 資訊
        )
        
        # 如果表單中有提供其他資訊，覆蓋 EXIF 資訊
        if 'date_taken' in request.form:
            try:
                photo.date_taken = datetime.strptime(request.form['date_taken'], '%Y-%m-%d')
            except ValueError:
                pass
                
        if 'photographer' in request.form:
            photo.photographer = request.form['photographer']
            
        if 'description' in request.form:
            photo.description = request.form['description']
        
        db.session.add(photo)
        db.session.commit()
        
        return jsonify({
            'message': '照片上傳成功',
            'photo': photo.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"上傳照片時發生錯誤: {str(e)}")
        return jsonify({'error': '上傳照片時發生錯誤'}), 500

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
        # 檢查照片記錄是否存在且已核准
        photo = Photo.query.filter_by(filename=filename).first()
        if not photo:
            current_app.logger.warning(f"照片記錄不存在: {filename}")
            return "照片不存在", 404
            
        if not photo.is_approved and not current_user.is_authenticated:
            current_app.logger.info(f"未核准的照片訪問被拒絕: {filename}")
            return "照片未核准", 403
            
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            current_app.logger.error(f"照片檔案遺失: {filename}")
            return "照片檔案遺失", 404
            
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        current_app.logger.error(f"讀取照片時發生錯誤 {filename}: {str(e)}")
        return "讀取照片時發生錯誤", 500
