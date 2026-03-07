# 快速開始指南

## 系統功能

1. 多 API 輪換 + 多模型集成決策
2. 本地持久化配置（關閉後仍保留）
3. API Keys 加密存儲
4. 實時追蹤 API 使用狀況
5. 自動故障轉移

## 安裝步驟

### 1. 更新代碼

```bash
cd STW
git pull origin main
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

新增的依賴：
- `cryptography` - 用於 API Keys 加密
- `google-generativeai` - Google Gemini API

### 3. 注冊免費 API

至少需要 2 個 API Key（建議 Groq + Google）：

#### A. Groq (必須 - 速度最快)
1. 訪問 https://console.groq.com
2. 點擊 "Sign Up" 注冊
3. 選擇 "API Keys" -> "Create API Key"
4. 複製 API Key（以 `gsk_` 開頭）

#### B. Google Gemini (必須 - 推理最強)
1. 訪問 https://aistudio.google.com
2. 登入 Google 帳號
3. 點擊 "Get API Key" -> "Create API Key"
4. 複製 API Key（以 `AIzaSy` 開頭）

#### C. OpenRouter (選填 - 多模型)
1. 訪問 https://openrouter.ai
2. 點擊 "Sign In" 登入
3. 選擇 "Keys" -> "Create Key"
4. 複製 API Key（以 `sk-or-v1-` 開頭）

### 4. 啟動系統

```bash
python app_flask.py
```

啟動後你會看到：
```
Running on http://127.0.0.1:5000
```

### 5. 配置 API Keys

1. 打開流覽器訪問 http://localhost:5000
2. 點擊右側選單的 "設定"
3. 滾動到 "免費 API 設定" 區域
4. 輸入你的 API Keys：
   - Groq API Key
   - Google Gemini API Key
   - OpenRouter API Key (選填)
5. 點擊 "保存設定"

保存後，你會看到：
- API Keys 欄位變成 "•••••••• (已保存)"
- 下方顯示 API 統計表格

### 6. 測試連接

點擊 "測試 API 連接" 按鈕，系統會：
- 嘗試連接所有配置的 API
- 顯示可用/不可用的 API
- 更新統計表格

## 使用教學

### 單模型模式

1. 在 "設定" 中，關閉 "啟用集成決策"
2. 系統會自動選擇最优 API（根據優先級）
3. 每次請求只使用 1 個模型

### 多模型投票模式

1. 在 "設定" 中，啟用 "啟用集成決策"
2. 設定 最少模型數 = 2
3. 設定 最多模型數 = 3
4. 每次請求會同時調用 2-3 個模型
5. 系統會投票決定最終動作

### 自動更新設定

1. 點擊 "自動更新" 頁籤
2. 選擇交易對、周期、頁率
3. 啟用 "啟用自動更新" 開關
4. 系統每 15 分鐘自動分析一次

### 查看 API 使用情況

在 "設定" 頁面下方會顯示：
- 總 API 數
- 可用 API 數
- 每個 API 的每日使用量
- API 狀態（正常/不可用）

## 常見問題

### Q1: 關閉流覽器後配置會消失嗎？

A: 不會。配置保存在本地文件（config.json），重新打開後會自動載入。

### Q2: 關閉 app_flask.py 後配置還在嗎？

A: 在。所有配置持久化存儲，下次啟動自動載入。

### Q3: 我只有 1 個 API Key，能用嗎？

A: 可以，但建議至少 2 個（Groq + Gemini）以保證穩定性。

### Q4: API Keys 安全嗎？

A: 相對安全：
- 使用 Fernet 對稱加密
- 密鑰文件 (.config_key) 設置 600 權限
- 不會提交到 Git (已在 .gitignore)

### Q5: 每天可以無限使用嗎？

A: 有免費额度限制：
- Groq: 14,400 次/天
- Google Gemini: 1,500 次/天
- OpenRouter: 1,000 次/天

你每 15 分鐘只請求一次（每天 96 次），遠低於限制。

### Q6: 如何備份配置？

A: 兩種方式：
1. 點擊 "匯出配置" 按鈕
2. 手動複製 config.json 和 .config_key

### Q7: 換電腦後怎麼辦？

A: 複製這兩個文件到新電腦：
```bash
cp config.json /path/to/new/location/
cp .config_key /path/to/new/location/
```

## 一分鐘快速設定

```bash
# 1. 更新代碼
git pull origin main

# 2. 安裝依賴
pip install cryptography google-generativeai

# 3. 啟動系統
python app_flask.py

# 4. 打開流覽器
http://localhost:5000

# 5. 點擊 "設定" -> 輸入 API Keys -> 保存

# 6. 點擊 "測試 API 連接"

# 7. 開始使用！
```

## 下一步

1. 查看 [docs/MULTI_API_SETUP.md](docs/MULTI_API_SETUP.md) 了解多 API 詳細設定
2. 查看 [docs/CONFIG_SETUP.md](docs/CONFIG_SETUP.md) 了解配置管理
3. 點擊 "自動更新" 啟用定時分析
4. 點擊 "學習案例庫" 添加成功交易案例

## 文件結構

```
STW/
├── app_flask.py          # 主程式
├── api_routes_config.py  # 配置 API 路由
├── config.json           # 配置文件 (加密)
├── .config_key          # 加密密鑰 (不提交)
├── api_config.json      # API 管理器狀態
├── core/
│   ├── config_manager.py      # 配置管理器
│   ├── multi_api_manager.py   # 多 API 管理
│   ├── multi_model_ensemble.py # 多模型集成
│   └── llm_agent_ensemble.py  # 增強版 Agent
├── docs/
│   ├── MULTI_API_SETUP.md   # 多 API 設定指南
│   └── CONFIG_SETUP.md      # 配置設定說明
└── ...
```

## 注意事項

1. 不要刪除 .config_key，否則無法解密 config.json
2. 不要將 config.json 和 .config_key 提交到 Git
3. 備份時需要同時備份兩個文件
4. 首次使用必須輸入 API Keys
5. 建議至少配置 2 個 API 以保證穩定性

## 幫助

遇到問題？
1. 查看 docs/ 目錄中的詳細文檔
2. 檢查是否有 config.json 和 .config_key
3. 嘗試點擊 "測試 API 連接" 按鈕
4. 檢查終端輸出的錯誤訊息
