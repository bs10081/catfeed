# 專案結構說明

## 目錄結構

```
catfeed/
├── catfeed/                # 主應用目錄
│   ├── __init__.py        # 應用初始化
│   ├── models/            # 數據模型
│   │   ├── __init__.py
│   │   ├── admin.py      # 管理員模型
│   │   ├── biography.py   # 貓咪簡介模型
│   │   ├── cat_profile.py # 貓咪資料模型
│   │   ├── feeding_record.py # 餵食記錄模型
│   │   ├── photo.py      # 照片模型
│   │   └── settings.py   # 系統設定模型
│   ├── routes/           # 路由處理
│   │   ├── __init__.py
│   │   ├── admin.py      # 管理員相關路由
│   │   ├── auth.py       # 認證相關路由
│   │   ├── feeding.py    # 餵食記錄相關路由
│   │   ├── main.py       # 主頁面路由
│   │   └── photos.py     # 照片相關路由
│   ├── static/           # 靜態文件
│   │   ├── css/         # 樣式文件
│   │   ├── js/          # JavaScript 文件
│   │   └── uploads/     # 上傳的文件
│   ├── templates/        # 模板文件
│   │   ├── admin/       # 管理員頁面模板
│   │   ├── auth/        # 認證頁面模板
│   │   └── main/        # 主要頁面模板
│   └── utils/           # 工具函數
│       ├── limiter.py   # 請求限制器
│       └── password_validator.py # 密碼驗證器
└── tests/               # 測試文件
```

## 核心組件說明

### 模型 (Models)

1. **FeedingRecord** (`models/feeding_record.py`)
   - 記錄餵食信息
   - 包含餵食時間、食物類型、份量等信息
   - 支持編輯和刪除功能（限15分鐘內）

2. **CatProfile** (`models/cat_profile.py`)
   - 存儲貓咪基本信息
   - 包含名字、年齡、品種等信息

3. **Photo** (`models/photo.py`)
   - 管理貓咪照片
   - 支持照片上傳、查看和刪除

### 路由 (Routes)

1. **餵食記錄** (`routes/feeding.py`)
   - 處理餵食記錄的添加、編輯、刪除
   - 提供餵食統計數據
   - 支持訪客操作（使用 session_id 追蹤）

2. **照片管理** (`routes/photos.py`)
   - 處理照片上傳
   - 提供照片查看功能
   - 管理照片存儲和刪除

3. **主頁面** (`routes/main.py`)
   - 渲染主頁面
   - 顯示最近的餵食記錄
   - 整合照片展示功能

### 工具 (Utils)

1. **請求限制器** (`utils/limiter.py`)
   - 防止請求過於頻繁
   - 保護 API 端點

2. **密碼驗證器** (`utils/password_validator.py`)
   - 確保密碼符合安全要求
   - 用於管理員帳戶管理

## 前端結構

### 模板 (Templates)

1. **base.html**
   - 基礎模板
   - 包含共用的頁面結構和導航欄

2. **main/index.html**
   - 主頁面模板
   - 餵食記錄表單
   - 最近餵食記錄列表
   - 照片展示區域

### 靜態文件 (Static)

1. **CSS**
   - Bootstrap 5 樣式
   - 自定義樣式

2. **JavaScript**
   - 表單處理
   - AJAX 請求
   - 照片上傳處理
   - 動態頁面更新

## 安全性考慮

1. **訪客追蹤**
   - 使用 session_id 追蹤訪客
   - 限制編輯和刪除權限

2. **請求限制**
   - 防止 API 濫用
   - 保護服務器資源

3. **文件上傳**
   - 驗證文件類型
   - 限制文件大小
   - 安全的文件存儲
