"""添加密碼策略相關欄位

此腳本將為 Admin 表添加密碼策略相關的欄位。
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys
import os
from sqlalchemy import text

# 獲取專案根目錄的絕對路徑
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'catfeed.db')

# 創建一個新的 Flask 應用和資料庫實例
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
db = SQLAlchemy(app)

def upgrade():
    """執行資料庫升級"""
    # 添加新欄位
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # 先檢查表是否存在
                conn.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='admin';
                """))
                
                # 創建臨時表
                conn.execute(text("""
                CREATE TABLE admin_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    password_hash VARCHAR(120) NOT NULL,
                    last_password_change DATETIME,
                    password_history JSON,
                    failed_login_attempts INTEGER DEFAULT 0,
                    last_failed_login DATETIME,
                    account_locked_until DATETIME,
                    force_password_change BOOLEAN DEFAULT 1
                );
                """))
                
                # 複製現有數據
                conn.execute(text("""
                INSERT INTO admin_new (id, username, password_hash)
                SELECT id, username, password_hash FROM admin;
                """))
                
                # 更新時間戳和其他欄位
                conn.execute(text("""
                UPDATE admin_new SET 
                    last_password_change = CURRENT_TIMESTAMP,
                    password_history = '[]',
                    failed_login_attempts = 0,
                    force_password_change = 1;
                """))
                
                # 刪除舊表並重命名新表
                conn.execute(text("DROP TABLE admin;"))
                conn.execute(text("ALTER TABLE admin_new RENAME TO admin;"))
                
                # 提交事務
                conn.commit()
                
            print("資料庫升級完成")
            
        except Exception as e:
            print(f"錯誤：{str(e)}")
            raise

def downgrade():
    """執行資料庫降級（回滾）"""
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # 創建臨時表，只保留原始欄位
                conn.execute(text("""
                CREATE TABLE admin_old (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    password_hash VARCHAR(120) NOT NULL
                );
                """))
                
                # 複製必要的數據
                conn.execute(text("""
                INSERT INTO admin_old (id, username, password_hash)
                SELECT id, username, password_hash FROM admin;
                """))
                
                # 刪除新表並重命名舊表
                conn.execute(text("DROP TABLE admin;"))
                conn.execute(text("ALTER TABLE admin_old RENAME TO admin;"))
                
                # 提交事務
                conn.commit()
                
            print("資料庫降級完成")
            
        except Exception as e:
            print(f"錯誤：{str(e)}")
            raise

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        downgrade()
    else:
        upgrade()
