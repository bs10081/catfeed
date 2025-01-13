import sqlite3
from datetime import datetime
from catfeed import create_app, db
from catfeed.models import Admin, FeedingRecord, CatProfile, Settings, Biography

def parse_datetime(dt_str):
    """解析各種可能的日期時間格式"""
    try:
        # 首先嘗試標準格式
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            # 嘗試帶有毫秒的格式
            return datetime.strptime(dt_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        except (ValueError, IndexError):
            # 如果都失敗了，返回當前時間
            print(f"無法解析日期時間: {dt_str}，使用當前時間")
            return datetime.now()

def migrate_all_data():
    app = create_app()
    
    # 連接備份資料庫
    backup_conn = sqlite3.connect('instance/catfeed.db.backup')
    backup_cur = backup_conn.cursor()
    
    with app.app_context():
        # 1. 遷移管理員帳戶
        print("遷移管理員帳戶...")
        backup_cur.execute('SELECT username, password_hash FROM admin')
        admin_data = backup_cur.fetchall()
        
        for username, password_hash in admin_data:
            admin = Admin.query.filter_by(username=username).first()
            if not admin:
                admin = Admin(username=username, password_hash=password_hash)
                db.session.add(admin)
                print(f"添加管理員: {username}")
        
        # 2. 遷移餵食記錄
        print("\n遷移餵食記錄...")
        backup_cur.execute('''
            SELECT timestamp, food_type, amount, unit, calories, notes, feeder_nickname 
            FROM feeding_record
        ''')
        feeding_data = backup_cur.fetchall()
        
        for timestamp, food_type, amount, unit, calories, notes, feeder_nickname in feeding_data:
            record = FeedingRecord.query.filter_by(
                timestamp=parse_datetime(timestamp),
                feeder_nickname=feeder_nickname
            ).first()
            
            if not record:
                record = FeedingRecord(
                    timestamp=parse_datetime(timestamp),
                    food_type=food_type,
                    amount=amount,
                    unit=unit,
                    calories=calories,
                    notes=notes,
                    feeder_nickname=feeder_nickname
                )
                db.session.add(record)
                print(f"添加餵食記錄: {timestamp} - {feeder_nickname}")
        
        # 3. 遷移貓咪檔案
        print("\n遷移貓咪檔案...")
        backup_cur.execute('SELECT weight, is_neutered, activity_level FROM cat_profile')
        cat_data = backup_cur.fetchall()
        
        for weight, is_neutered, activity_level in cat_data:
            profile = CatProfile.query.first()
            if not profile:
                profile = CatProfile(
                    weight=weight,
                    neutered=bool(is_neutered),
                    activity_level=activity_level
                )
                db.session.add(profile)
                print(f"添加貓咪檔案: 體重={weight}, 結紮={is_neutered}, 活動量={activity_level}")
        
        # 4. 遷移設定
        print("\n遷移設定...")
        backup_cur.execute('SELECT timezone FROM settings')
        settings_data = backup_cur.fetchall()
        
        for (timezone,) in settings_data:
            settings = Settings.query.first()
            if not settings:
                settings = Settings(timezone=timezone)
                db.session.add(settings)
                print(f"添加設定: 時區={timezone}")
        
        # 5. 遷移生平記事
        print("\n遷移生平記事...")
        backup_cur.execute('''
            SELECT date, content, created_at, updated_at 
            FROM biography
        ''')
        bio_data = backup_cur.fetchall()
        
        for date, content, created_at, updated_at in bio_data:
            bio = Biography.query.filter_by(
                date=parse_datetime(date)
            ).first()
            
            if not bio:
                bio = Biography(
                    date=parse_datetime(date),
                    content=content,
                    created_at=parse_datetime(created_at),
                    updated_at=parse_datetime(updated_at)
                )
                db.session.add(bio)
                print(f"添加生平記事: {date}")
        
        # 提交所有更改
        try:
            db.session.commit()
            print("\n遷移完成！")
        except Exception as e:
            db.session.rollback()
            print(f"\n遷移失敗: {str(e)}")
    
    backup_conn.close()

if __name__ == '__main__':
    migrate_all_data()
