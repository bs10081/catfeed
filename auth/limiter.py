"""請求頻率限制模組

此模組提供請求頻率限制功能，用於防止暴力破解和 DoS 攻擊。
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from flask import request, jsonify, current_app
import redis

def get_redis_client():
    """獲取 Redis 客戶端實例"""
    try:
        return redis.Redis(
            host=current_app.config.get('REDIS_HOST', 'localhost'),
            port=current_app.config.get('REDIS_PORT', 6379),
            db=current_app.config.get('REDIS_DB', 0),
            decode_responses=True
        )
    except redis.ConnectionError:
        current_app.logger.warning("無法連接到 Redis，將使用內存存儲")
        return None

def init_limiter(app):
    """初始化限制器"""
    storage_url = "memory://"
    if app.config.get('REDIS_ENABLED'):
        redis_host = app.config.get('REDIS_HOST', 'localhost')
        redis_port = app.config.get('REDIS_PORT', 6379)
        redis_db = app.config.get('REDIS_DB', 0)
        storage_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=storage_url,
        strategy="fixed-window",  # 固定時間窗口策略
        default_limits=["200 per day", "50 per hour"]  # 默認限制
    )
    
    return limiter

def rate_limit_by_ip(limit_string):
    """基於 IP 的請求限制裝飾器"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # 獲取當前的限制器實例
            limiter = current_app.extensions['limiter']
            
            # 應用限制
            limiter.limit(limit_string)(f)(*args, **kwargs)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def rate_limit_by_user(limit_string):
    """基於用戶的請求限制裝飾器"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            from flask_login import current_user
            
            # 獲取當前的限制器實例
            limiter = current_app.extensions['limiter']
            
            # 如果用戶已登入，使用用戶 ID 作為鍵
            if current_user.is_authenticated:
                key = f"user:{current_user.id}"
            else:
                key = get_remote_address()
            
            # 應用限制
            limiter.limit(
                limit_string,
                key_func=lambda: key
            )(f)(*args, **kwargs)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def block_ip(ip_address, duration):
    """封鎖特定 IP 地址一段時間
    
    Args:
        ip_address: 要封鎖的 IP 地址
        duration: 封鎖時間（秒）
    """
    redis_client = get_redis_client()
    if redis_client:
        key = f"blocked_ip:{ip_address}"
        redis_client.setex(key, duration, "1")

def is_ip_blocked(ip_address):
    """檢查 IP 是否被封鎖
    
    Args:
        ip_address: 要檢查的 IP 地址
        
    Returns:
        bool: 是否被封鎖
    """
    redis_client = get_redis_client()
    if redis_client:
        key = f"blocked_ip:{ip_address}"
        return bool(redis_client.exists(key))
    return False

def check_ip_block():
    """檢查 IP 封鎖的中間件"""
    def middleware():
        ip = get_remote_address()
        if is_ip_blocked(ip):
            return jsonify({
                "error": "您的 IP 已被暫時封鎖，請稍後再試"
            }), 429
    return middleware
