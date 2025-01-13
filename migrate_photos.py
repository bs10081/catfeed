import os
import shutil
from datetime import datetime
from catfeed import create_app, db
from catfeed.models import Photo
from PIL import Image
from PIL.ExifTags import TAGS

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
        print(f"提取 EXIF 資訊時發生錯誤: {str(e)}")
        return {}

def migrate_photos():
    app = create_app()
    with app.app_context():
        # 獲取原始和目標目錄
        src_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        dst_dir = app.config['UPLOAD_FOLDER']
        
        print(f"從 {src_dir} 遷移照片到 {dst_dir}")
        
        # 確保目標目錄存在
        os.makedirs(dst_dir, exist_ok=True)
        
        # 遍歷原始目錄中的所有檔案
        if os.path.exists(src_dir):
            for filename in os.listdir(src_dir):
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    continue
                    
                src_path = os.path.join(src_dir, filename)
                dst_path = os.path.join(dst_dir, filename)
                
                # 檢查檔案是否已經存在於資料庫
                photo = Photo.query.filter_by(filename=filename).first()
                
                if not photo:
                    # 提取 EXIF 資訊
                    exif_data = extract_exif_data(src_path)
                    
                    # 如果沒有拍攝日期，使用檔案建立時間
                    if 'date_taken' not in exif_data:
                        exif_data['date_taken'] = datetime.fromtimestamp(os.path.getctime(src_path))
                    
                    # 創建新的照片記錄
                    photo = Photo(
                        filename=filename,
                        original_filename=filename,
                        upload_date=datetime.fromtimestamp(os.path.getctime(src_path)),
                        file_size=os.path.getsize(src_path),
                        is_approved=True,  # 假設所有現有照片都是已核准的
                        **exif_data
                    )
                    db.session.add(photo)
                    print(f"添加照片記錄: {filename}")
                
                # 複製檔案到新位置
                if not os.path.exists(dst_path):
                    shutil.copy2(src_path, dst_path)
                    print(f"複製檔案: {filename}")
                else:
                    print(f"檔案已存在，跳過: {filename}")
            
            # 提交所有更改
            db.session.commit()
            print("遷移完成！")
        else:
            print(f"原始目錄不存在: {src_dir}")

if __name__ == '__main__':
    migrate_photos()
