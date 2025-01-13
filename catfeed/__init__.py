from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

# 初始化擴展，但還不配置它們
db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    from catfeed.models import User
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    
    # 載入環境變數
    load_dotenv()
    
    # 配置應用
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    
    # 確保 instance 目錄存在
    instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # 設置數據庫 URI
    db_path = os.path.join(instance_path, 'catfeed.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 設置上傳目錄
    upload_folder = os.path.join(instance_path, os.getenv('UPLOAD_FOLDER', 'uploads'))
    app.config['UPLOAD_FOLDER'] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)
    
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    
    # 初始化擴展
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)
    
    # 設定登入視圖
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '請先登入'
    login_manager.login_message_category = 'info'
    
    # 註冊藍圖
    from catfeed.routes import auth, admin, photos, feeding, main
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(photos.bp)
    app.register_blueprint(feeding.bp)
    app.register_blueprint(main.bp)
    
    # 創建資料庫表
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")
    
    return app
