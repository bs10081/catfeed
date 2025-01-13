import sqlite3
from catfeed import create_app, db
from catfeed.models import Photo

def migrate_descriptions():
    app = create_app()
    
    # 連接備份資料庫
    backup_conn = sqlite3.connect('instance/catfeed.db.backup')
    backup_cur = backup_conn.cursor()
    
    # 從備份資料庫讀取描述和攝影師資料
    backup_cur.execute('SELECT filename, description, photographer FROM photo')
    photo_data = backup_cur.fetchall()
    
    with app.app_context():
        # 更新每張照片的資訊
        for filename, description, photographer in photo_data:
            # 找到對應的照片記錄
            photo = Photo.query.filter_by(filename=filename).first()
            if photo:
                print(f"更新照片 {filename}:")
                print(f"  描述: {description}")
                print(f"  攝影師: {photographer}")
                
                # 更新資訊
                photo.description = description
                photo.photographer = photographer
        
        # 提交更改
        db.session.commit()
        print("遷移完成！")
    
    backup_conn.close()

if __name__ == '__main__':
    migrate_descriptions()
