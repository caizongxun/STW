# 配置設定說明

## 功能特點

1. 本地持久化存儲
   - 所有配置保存到 config.json
   - API Keys 加密存儲（使用 Fernet 對稱加密）
   - 關閉 app_flask.py 後配置仍保留
   - 重新打開頁面自動載入上次設定

2. 多 API 管理
   - 支持 5+ 免費 API 提供商
   - 實時顯示每個 API 使用狀況
   - 自動追蹤每日额度

3. 安全性
   - API Keys 加密存儲
   - 前端不顯示實際 Key（只顯示掩碼）
   - 加密密鑰存儲在 .config_key（不提交到 git）

## 使用步驟

### 1. 啟動系統

```bash
# 安裝依賴
pip install cryptography

# 啟動
python app_flask.py
```

### 2. 配置 API Keys

1. 點擊右側選單的「設定」
2. 滾動到「API 設定」區域
3. 輸入你的 API Keys：
   - Groq API Key
   - Google API Key
   - OpenRouter API Key
   - 等等...
4. 點擊「保存設定」

### 3. 驗證配置

保存後你會看到：
- API Keys 欄位變成 "•••••••• (已保存)"
- 下方顯示 API 統計表格
- 顯示可用 API 數量

### 4. 測試連接

點擊「測試 API 連接」按鈕，系統會：
- 嘗試連接所有配置的 API
- 顯示可用/不可用的 API
- 更新統計表格

## 配置文件結構

```json
{
  "ai_model": "deepseek-r1:14b",
  "ai_temperature": 0.1,
  "ai_max_tokens": 2048,
  "ai_confidence_threshold": 70,
  
  "enable_ensemble": true,
  "min_models": 2,
  "max_models": 3,
  
  "groq_api_key": "<加密字串>",
  "google_api_key": "<加密字串>",
  "openrouter_api_key": "<加密字串>",
  
  "enable_notifications": false,
  "notification_email": "",
  "notify_on_trade": false,
  "notify_on_error": false
}
```

## 常見問題

### Q1: 配置存儲在哪裡？

A: 存儲在兩個文件：
- `config.json` - 配置資料（API Keys 已加密）
- `.config_key` - 加密密鑰（不要刪除！）

### Q2: 關閉流覽器後配置會消失嗎？

A: 不會。配置保存在本地文件，即使關閉流覽器或 app_flask.py 也會保留。

### Q3: 如何備份配置？

A: 兩種方式：
1. 點擊「匯出配置」按鈕
2. 手動複製 `config.json` 和 `.config_key`

### Q4: 如何轉移到另一台電腦？

A: 複製這兩個文件到新電腦：
```bash
cp config.json /path/to/new/location/
cp .config_key /path/to/new/location/
```

### Q5: API Keys 安全嗎？

A: 相對安全：
- 使用 Fernet 對稱加密
- 密鑰文件設置 600 權限（僅擁有者可讀）
- 但建議不要將 config.json 和 .config_key 上傳到公開 repo

### Q6: 忘記密鑰怎麼辦？

A: 刪除 .config_key，系統會自動生成新密鑰，但需要重新輸入 API Keys。

## 文件結構

```
STW/
├── config.json          # 配置文件（加密）
├── .config_key         # 加密密鑰（不要提交）
├── api_config.json     # API 管理器狀態
├── .gitignore          # 已包含 config.json 和 .config_key
└── ...
```

## .gitignore 設定

確保你的 .gitignore 包含：

```gitignore
# 配置文件
config.json
.config_key
api_config.json

# 環境變量
.env
.env.local

# Python
__pycache__/
*.pyc
```

## 進階使用

### 使用 Python 程式讀取配置

```python
from core.config_manager import ConfigManager

config = ConfigManager()

# 獲取解密後的 API Key
groq_key = config.get_api_key('groq_api_key')

# 獲取一般配置
temperature = config.get('ai_temperature', 0.1)

# 保存新配置
config.set('enable_ensemble', True)
config.save()

# 匯出到環境變量
config.export_to_env()
```

### 手動編輯 config.json

不建議手動編輯，但如果必須：

```python
# 加密 API Key
from cryptography.fernet import Fernet
from pathlib import Path

with open('.config_key', 'rb') as f:
    key = f.read()

cipher = Fernet(key)
encrypted = cipher.encrypt(b'your-api-key').decode()
print(encrypted)
```

## 完整流程示例

```bash
# 1. 首次設定
python app_flask.py
# -> 打開 http://localhost:5000
# -> 點擊「設定」
# -> 輸入 API Keys
# -> 點擊「保存設定」

# 2. 關閉系統
Ctrl+C

# 3. 重新啟動
python app_flask.py
# -> 配置自動載入
# -> 不需重新輸入 API Keys

# 4. 重新整理電腦後
# -> config.json 和 .config_key 仍在
# -> 配置保留

# 5. 關閉流覽器再打開
# -> 頁面自動載入上次設定
# -> API Keys 顯示「已保存」
```

## 注意事項

1. 不要刪除 .config_key，否則無法解密 config.json
2. 不要將這兩個文件提交到 Git
3. 備份時需要同時備份兩個文件
4. 更換電腦時記得複製這兩個文件
