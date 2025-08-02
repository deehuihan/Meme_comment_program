# Excel 數據記錄功能說明

## 功能概述
已成功實現將用戶活動數據寫入Excel文件的功能。當用戶在socialmediatemplate應用中進行各種操作時，系統會自動記錄以下信息到Excel文件中：

## 內容分配策略
系統根據檔案名稱後綴將新聞內容分配到不同頁面：
- **發送者頁面 (sender)**: 顯示所有 `_1` 和 `_2` 檔案
  - High_Intentional_1.png, High_Intentional_2.png
  - High_Unintentional_1.png, High_Unintentional_2.png  
  - Low_Intentional_1.png, Low_Intentional_2.png
  - Low_Unintentional_1.png, Low_Unintentional_2.png

- **觀察者頁面 (receiver)**: 顯示所有 `_3` 和 `_4` 檔案
  - High_Intentional_3.png, High_Intentional_4.png
  - High_Unintentional_3.png, High_Unintentional_4.png
  - Low_Intentional_3.png, Low_Intentional_4.png
  - Low_Unintentional_3.png, Low_Unintentional_4.png

## Excel文件結構
文件名：`user_data.xlsx`
位置：應用根目錄

### 列結構：
1. **User ID** - 用戶ID
2. **Created Time** - 創建時間（格式：YYYY-MM-DD HH:MM:SS）
3. **Activity Type** - 活動類型
4. **Page** - 頁面名稱
5. **Details** - 詳細信息
6. **Timestamp** - 時間戳（數字格式）

## 記錄的活動類型

### 1. 用戶註冊 (user_registration)
- 當用戶在input.html頁面首次輸入用戶ID時記錄
- Page: input
- Details: "User created account and logged in"

### 2. 頁面進入 (page_entry)
- 當用戶進入index.html選擇頁面時記錄
- Page: index
- Details: "User entered index page"

### 3. 頁面瀏覽 (page_view)
- 當用戶瀏覽選擇頁面時記錄
- Page: index
- Details: "Viewed selection page"

### 4. 頁面導航 (page_navigation)
- 當用戶從index頁面導航到其他頁面時記錄
- Page: receiver 或 sender
- Details: "Navigate from index to [destination] page"

### 6. 內容分配 (content_allocation)
- 記錄用戶在不同頁面看到的新聞內容
- Page: receiver 或 sender
- Details: 具體看到的新聞檔案列表
- **發送者頁面**: 顯示 _1 和 _2 新聞檔案
- **觀察者頁面**: 顯示 _3 和 _4 新聞檔案

### 5. 用戶登出 (logout)
- 當用戶點擊登出按鈕時記錄
- Page: index
- Details: "User logged out from index page"

## API端點

### 記錄活動
- **URL**: `/api/log-activity`
- **方法**: POST
- **參數**:
  ```json
  {
    "user_id": "用戶ID",
    "activity_type": "活動類型",
    "page": "頁面名稱",
    "details": "詳細信息"
  }
  ```

### 獲取用戶活動
- **URL**: `/api/get-activities/<user_id>`
- **方法**: GET
- **返回**: 指定用戶的所有活動記錄

### 獲取所有數據
- **URL**: `/api/get-all-data`
- **方法**: GET
- **返回**: Excel文件中的所有數據

## 數據查看頁面
- **URL**: `http://127.0.0.1:5000/data-viewer`
- 提供Web界面查看、搜索和匯出Excel數據
- 顯示統計信息：總記錄數、不重複用戶數、今日記錄數
- 支持按用戶ID搜索
- 支持匯出為CSV格式

## 使用方式

1. **啟動應用**：
   ```bash
   cd "c:\Users\deehu\Desktop\Program\socialmediatemplate"
   python web.py
   ```

2. **訪問主頁面**：
   - 打開 `http://127.0.0.1:5000`
   - 輸入用戶ID進行註冊（會自動記錄到Excel）

3. **查看數據**：
   - 打開 `http://127.0.0.1:5000/data-viewer`
   - 查看所有用戶活動記錄

## 技術實現

### 後端 (Python/Flask)
- `excel_manager.py` - Excel文件管理模塊
- `web.py` - 增加了Excel記錄的API端點
- 使用 `openpyxl` 套件處理Excel文件
- 線程安全的文件寫入

### 前端 (JavaScript)
- `index.html` - 增加了Excel記錄功能
- `input.html` - 增加了用戶註冊記錄
- `data_viewer.html` - 數據查看界面

## 特色功能

1. **實時記錄** - 用戶操作即時寫入Excel
2. **雙重備份** - 同時記錄到Excel和Firebase
3. **線程安全** - 支持多用戶同時操作
4. **Web查看** - 提供友好的數據查看界面
5. **數據匯出** - 支持CSV格式匯出
6. **錯誤處理** - 完善的異常處理機制

## 注意事項

- Excel文件會在應用首次啟動時自動創建
- 每次用戶操作都會即時寫入，確保數據不丟失
- 建議定期備份Excel文件
- 數據查看頁面支持實時刷新

## 未來擴展

可以根據需要添加更多列，例如：
- IP地址
- 瀏覽器信息
- 會話持續時間
- 具體操作詳情
- 錯誤日誌等

## 內容分配功能測試

您可以使用以下方式驗證內容分配是否正確：

1. **檢查發送者頁面內容**：
   ```bash
   python -c "from web import get_news_files_for_page; print(get_news_files_for_page('sender'))"
   ```

2. **檢查觀察者頁面內容**：
   ```bash
   python -c "from web import get_news_files_for_page; print(get_news_files_for_page('receiver'))"
   ```

3. **查看數據記錄**：
   - 訪問 `http://127.0.0.1:5000/data-viewer`
   - 查找 `content_allocation` 活動類型的記錄
   - 確認不同用戶在不同頁面看到的內容被正確記錄
