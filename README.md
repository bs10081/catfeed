# CatFeed - 貓咪餵食記錄系統

一個簡單易用的貓咪餵食記錄系統，幫助你追蹤和管理貓咪的餵食情況。無需註冊即可使用，支持照片上傳和餵食統計。

## 功能特點

- 🐱 無需註冊，訪客即可記錄餵食
- 📝 記錄餵食時間、食物類型和份量
- 📊 餵食統計和趨勢分析
- 📸 上傳和管理貓咪照片
- 🔒 15分鐘內可編輯或刪除記錄
- 📱 響應式設計，支持手機訪問

## 快速開始

### 系統要求

- Python 3.8+
- pip
- 虛擬環境（推薦）

### 安裝步驟

1. 克隆專案
```bash
git clone https://github.com/yourusername/catfeed.git
cd catfeed
```

2. 創建並啟動虛擬環境
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安裝依賴
```bash
pip install -r requirements.txt
```

4. 設置環境變數
```bash
cp .env.example .env
# 編輯 .env 文件，設置必要的環境變數
```

5. 初始化數據庫
```bash
flask db upgrade
python generate_secret_key.py
```

6. 啟動應用
```bash
flask run
```

訪問 http://localhost:5000 開始使用！

## 使用指南

### 記錄餵食

1. 在首頁填寫餵食表單
2. 輸入：
   - 餵食人暱稱（可選）
   - 食物類型
   - 餵食量（克）
   - 卡路里（可選）
   - 備註（可選）
3. 提交表單

### 管理記錄

- 15分鐘內可編輯或刪除自己的記錄
- 可以查看歷史記錄和統計數據
- 支持按日期和時間篩選記錄

### 照片管理

- 支持上傳貓咪照片
- 可以為照片添加描述
- 支持瀏覽和刪除照片

### 管理員功能

- 系統設置
- 貓咪資料管理
- 查看所有餵食記錄
- 管理照片庫

## API 文檔

詳細的 API 文檔請參考 [docs/API.md](docs/API.md)。

## 項目結構

關於項目結構的詳細說明，請參考 [docs/STRUCTURE.md](docs/STRUCTURE.md)。

## 貢獻指南

1. Fork 本專案
2. 創建新的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 授權協議

本專案採用 MIT 授權協議 - 詳見 [LICENSE](LICENSE) 文件

## 聯繫方式

如有任何問題或建議，歡迎提出 Issue 或 Pull Request。

## 致謝

感謝所有為這個項目做出貢獻的開發者！
