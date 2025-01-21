import sqlite3
from app import app, db
import shutil
import os
from datetime import datetime

def migrate_data():
    # 確保新的資料庫結構存在
    with app.app_context():
        db.create_all()
        
    # 連接到備份的資料庫
    backup_conn = sqlite3.connect('instance/catfeed.db.backup')
    backup_cur = backup_conn.cursor()
    
    # 連接到新的資料庫
    new_conn = sqlite3.connect('instance/catfeed.db')
    new_cur = new_conn.cursor()
    
    try:
        # 清除新資料庫中的現有資料
        new_cur.execute("DELETE FROM feeding_record")
        new_cur.execute("DELETE FROM cat_profile")
        new_cur.execute("DELETE FROM settings")
        new_cur.execute("DELETE FROM admin")
        new_cur.execute("DELETE FROM biography")
        new_cur.execute("DELETE FROM photo")
        new_conn.commit()
        
        # 遷移餵食記錄
        backup_cur.execute("SELECT * FROM feeding_record")
        records = backup_cur.fetchall()
        for record in records:
            new_cur.execute(
                "INSERT INTO feeding_record (id, timestamp, food_type, amount, unit, calories, notes, feeder_nickname) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                record
            )
        
        # 遷移貓咪檔案
        backup_cur.execute("SELECT * FROM cat_profile")
        profiles = backup_cur.fetchall()
        for profile in profiles:
            new_cur.execute(
                "INSERT INTO cat_profile (id, weight, is_neutered, activity_level) VALUES (?, ?, ?, ?)",
                profile
            )
        
        # 遷移設定
        backup_cur.execute("SELECT * FROM settings")
        settings = backup_cur.fetchall()
        for setting in settings:
            new_cur.execute(
                "INSERT INTO settings (id, timezone) VALUES (?, ?)",
                setting
            )
            
        # 遷移管理員帳號，並設定新欄位的預設值
        backup_cur.execute("SELECT * FROM admin")
        admins = backup_cur.fetchall()
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        for admin in admins:
            new_cur.execute(
                """INSERT INTO admin 
                   (id, username, password_hash, last_password_change, 
                    password_history, failed_login_attempts, 
                    last_failed_login, account_locked_until, 
                    force_password_change)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (admin[0], admin[1], admin[2], current_time, 
                 '[]', 0, None, None, True)
            )
            
        # 遷移生平記事
        backup_cur.execute("SELECT * FROM biography")
        biographies = backup_cur.fetchall()
        for bio in biographies:
            new_cur.execute(
                """INSERT INTO biography 
                   (id, date, content, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                bio
            )
            
        # 遷移照片資料
        backup_cur.execute("SELECT * FROM photo")
        photos = backup_cur.fetchall()
        for photo in photos:
            new_cur.execute(
                """INSERT INTO photo 
                   (id, filename, original_filename, date_taken, 
                    description, photographer, upload_date, is_approved)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                photo
            )
            
        # 提交更改
        new_conn.commit()
        print("資料遷移完成！")
        
    except Exception as e:
        print(f"遷移過程中發生錯誤：{str(e)}")
        new_conn.rollback()
    finally:
        backup_conn.close()
        new_conn.close()

if __name__ == '__main__':
    migrate_data() 