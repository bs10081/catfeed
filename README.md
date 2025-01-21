q# 貓咪餵食記錄系統

這是一個用於記錄貓咪餵食情況的網頁應用程式。

## 功能特點

- 記錄每次餵食的時間、食物類型和份量
- 計算每日卡路里攝入量
- 追蹤貓咪體重變化
- 支援多個餵食者的記錄
- 照片上傳和管理功能
- 生平記事管理
- 基於 Redis 的速率限制保護

## 系統需求

- Python 3.8+
- SQLite3
- Redis (用於速率限制)
- Docker 和 Docker Compose (可選，用於運行 Redis)

## 開發環境安裝

1. 克隆專案：
   ```bash
   git clone https://github.com/yourusername/catfeed.git
   cd catfeed
   ```

2. 建立虛擬環境：
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或
   .venv\Scripts\activate  # Windows
   ```

3. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```

4. 設定環境變數：
   ```bash
   cp .env.example .env
   # 編輯 .env 檔案，設定必要的環境變數
   python generate_secret_key.py  # 生成 Flask Secret Key
   ```

5. 啟動 Redis（選擇其中一種方式）：
   
   使用 Docker Compose：
   ```bash
   docker-compose up -d
   ```
   
   或直接安裝 Redis：
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   ```

6. 初始化資料庫：
   ```bash
   python -c "from app import db; db.create_all()"
   ```

7. 運行開發伺服器：
   ```bash
   python app.py
   ```

## 生產環境部署

1. 安裝額外的依賴：
   ```bash
   pip install gunicorn
   ```

2. 設定檔案權限：
   ```bash
   chmod +x start.sh
   mkdir -p logs
   chmod 755 logs
   ```

3. 安裝系統服務：
   ```bash
   sudo cp catfeed.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable catfeed
   sudo systemctl start catfeed
   ```

4. 檢查服務狀態：
   ```bash
   sudo systemctl status catfeed
   ```

5. 查看日誌：
   ```bash
   # 應用程式日誌
   tail -f logs/access.log
   tail -f logs/error.log
   
   # 系統服務日誌
   sudo journalctl -u catfeed -f
   ```

應用程式將在 http://localhost:8080 運行。在生產環境中，建議使用 Nginx 作為反向代理來提供 HTTPS 支援。

## 預設管理員帳號

- 使用者名稱：admin
- 密碼：catfeed2024@TW

首次登入後，系統會要求更改密碼。

## 速率限制設定

系統使用 Redis 實現速率限制功能，預設限制如下：
- API 呼叫：30次/分鐘
- 登入嘗試：5次/分鐘
- 註冊：2次/小時
- 一般請求：200次/天

可以在 `.env` 檔案中調整這些設定。

## 資料備份

系統會自動在 `instance` 目錄下建立 SQLite 資料庫檔案。建議定期備份該檔案：

```bash
cp instance/catfeed.db instance/catfeed.db.backup
```

## 安全性功能

- 密碼強度檢查
- 登入失敗次數限制
- IP 封鎖機制
- 強制定期更改密碼
- 密碼歷史記錄檢查

## 注意事項

- 請確保 `uploads` 和 `logs` 目錄具有適當的寫入權限
- 在生產環境中使用 HTTPS
- 定期備份資料庫和上傳的檔案
- 在生產環境中修改預設的管理員密碼
- 定期檢查系統和套件更新

## 授權

MIT License
