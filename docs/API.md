# API 文檔

## 餵食記錄 API

### 添加餵食記錄
- **端點**: `/feeding/add`
- **方法**: POST
- **請求格式**: JSON
- **請求參數**:
  ```json
  {
    "feeder_nickname": "餵食人暱稱（可選，默認為'訪客'）",
    "food_type": "食物類型（必填）",
    "amount": "餵食量，單位為克（必填）",
    "calories": "卡路里（可選）",
    "notes": "備註（可選）"
  }
  ```
- **響應格式**: JSON
- **成功響應** (201):
  ```json
  {
    "message": "記錄添加成功",
    "record": {
      "id": "記錄ID",
      "timestamp": "記錄時間",
      "amount": "餵食量",
      "food_type": "食物類型",
      "calories": "卡路里",
      "notes": "備註",
      "feeder_nickname": "餵食人暱稱",
      "session_id": "會話ID",
      "can_edit": "是否可編輯"
    }
  }
  ```
- **錯誤響應** (400/404/500):
  ```json
  {
    "error": "錯誤信息"
  }
  ```

### 編輯餵食記錄
- **端點**: `/feeding/edit/<record_id>`
- **方法**: PUT
- **請求格式**: JSON
- **請求參數**: 同添加記錄
- **響應格式**: JSON
- **成功響應** (200):
  ```json
  {
    "message": "記錄更新成功",
    "record": {
      // 記錄詳情，同添加記錄響應
    }
  }
  ```

### 刪除餵食記錄
- **端點**: `/feeding/delete/<record_id>`
- **方法**: DELETE
- **響應格式**: JSON
- **成功響應** (200):
  ```json
  {
    "message": "記錄刪除成功"
  }
  ```

### 獲取今日餵食記錄
- **端點**: `/feeding/today`
- **方法**: GET
- **響應格式**: JSON
- **成功響應** (200):
  ```json
  {
    "records": [
      // 記錄列表，每個記錄格式同添加記錄響應
    ]
  }
  ```

### 獲取餵食統計
- **端點**: `/feeding/stats`
- **方法**: GET
- **響應格式**: JSON
- **成功響應** (200):
  ```json
  {
    "daily_stats": {
      // 每日統計數據
    },
    "weekly_stats": {
      // 每週統計數據
    },
    "monthly_stats": {
      // 每月統計數據
    }
  }
  ```

## 照片管理 API

### 上傳照片
- **端點**: `/photos/upload`
- **方法**: POST
- **請求格式**: multipart/form-data
- **請求參數**:
  - `photo`: 照片文件
  - `description`: 照片描述（可選）
- **響應格式**: JSON
- **成功響應** (201):
  ```json
  {
    "message": "照片上傳成功",
    "photo": {
      "id": "照片ID",
      "filename": "文件名",
      "description": "描述",
      "upload_time": "上傳時間"
    }
  }
  ```

### 查看照片
- **端點**: `/photos/view/<filename>`
- **方法**: GET
- **響應格式**: 圖片文件

### 刪除照片
- **端點**: `/photos/delete/<filename>`
- **方法**: DELETE
- **響應格式**: JSON
- **成功響應** (200):
  ```json
  {
    "message": "照片刪除成功"
  }
  ```

## 認證 API

### 登入
- **端點**: `/auth/login`
- **方法**: POST
- **請求格式**: JSON
- **請求參數**:
  ```json
  {
    "username": "用戶名",
    "password": "密碼"
  }
  ```
- **響應格式**: JSON
- **成功響應** (200):
  ```json
  {
    "message": "登入成功"
  }
  ```

### 修改密碼
- **端點**: `/auth/change_password`
- **方法**: POST
- **請求格式**: JSON
- **請求參數**:
  ```json
  {
    "current_password": "當前密碼",
    "new_password": "新密碼",
    "confirm_password": "確認新密碼"
  }
  ```
- **響應格式**: JSON
- **成功響應** (200):
  ```json
  {
    "message": "密碼修改成功"
  }
  ```

### 登出
- **端點**: `/auth/logout`
- **方法**: GET
- **響應格式**: JSON
- **成功響應** (200):
  ```json
  {
    "message": "登出成功"
  }
  ```

## 管理員 API

### 系統設定
- **端點**: `/admin/settings`
- **方法**: GET/POST
- **請求格式**: JSON
- **請求參數** (POST):
  ```json
  {
    "site_title": "網站標題",
    "cat_name": "貓咪名字",
    "cat_birthday": "貓咪生日",
    "cat_breed": "貓咪品種"
  }
  ```
- **響應格式**: JSON
- **成功響應** (200):
  ```json
  {
    "message": "設定更新成功",
    "settings": {
      "site_title": "網站標題",
      "cat_name": "貓咪名字",
      "cat_birthday": "貓咪生日",
      "cat_breed": "貓咪品種"
    }
  }
  ```

### 貓咪簡介管理
- **端點**: `/admin/biography`
- **方法**: GET/POST
- **請求格式**: JSON
- **請求參數** (POST):
  ```json
  {
    "content": "簡介內容",
    "display_order": "顯示順序"
  }
  ```
- **響應格式**: JSON
- **成功響應** (200):
  ```json
  {
    "message": "簡介更新成功"
  }
  ```
