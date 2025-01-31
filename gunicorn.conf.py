import multiprocessing

# 綁定的 IP 和端口
bind = "0.0.0.0:8080"

# 工作進程數量
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "sync"

# 每個工作進程的最大請求數
max_requests = 1000
max_requests_jitter = 50

# 超時設定
timeout = 300
keepalive = 2

# 緩衝區設定
limit_request_line = 0
limit_request_fields = 100
limit_request_field_size = 0

# 日誌設定
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 進程名稱
proc_name = "catfeed"

# 守護進程模式
daemon = False

# 環境變數
raw_env = [
    "FLASK_APP=app:app",
    "FLASK_ENV=production"
]

# 優化設定
worker_tmp_dir = '/dev/shm'
sendfile = True

# 綁定設定
backlog = 2048

# 工作進程設定
worker_connections = 1000 