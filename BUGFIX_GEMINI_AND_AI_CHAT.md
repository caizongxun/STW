# Gemini API 和 AI 聊天室修復說明

## 修復時間
2026-03-07 21:18 CST

## 問題描述

### 1. Gemini_Flash_B1 卡住問題
- **現象**: 在執行 AI 分析時，`[Gemini_Flash_B1] 分析中...` 之後就沒有結果了
- **原因**: 
  - Gemini API 調用超時，沒有設置 `timeout` 參數
  - 錯誤處理不完整，異常沒有被正確捕獲
  - 缺少重試機制

### 2. favicon.ico 404 錯誤
- **現象**: 瀏覽器控制台顯示 `GET /favicon.ico HTTP/1.1 404`
- **原因**: 沒有提供 favicon 圖示

### 3. AI 聊天室介面缺失
- **現象**: 需要在主頁面底下添加 AI 聊天室風格介面
- **需求**: 類似微信聊天室風格，顯示所有 AI 模型的完整回應

---

## 修復內容

### 1. 修復 Gemini API 超時問題

檔案: `core/arbitrator_consensus_agent.py`

#### 更新的 `GeminiModel` 類別：

```python
class GeminiModel(ModelInterface):
    """
    Gemini 模型封裝
    修復: 添加超時保護 + 重試機制 + 更詳細的錯誤處理
    """
    def analyze(self, system_prompt: str, user_prompt: str, max_retries: int = 2) -> Dict:
        for attempt in range(max_retries):
            try:
                # ... 省略 ...
                
                # 使用 generate_content 並設定超時
                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.2,
                        max_output_tokens=4000
                    ),
                    request_options={'timeout': 60}  # 60秒超時
                )
                # ... 省略 ...
```

#### 主要改進：

1. **超時保護**
   - 添加 `request_options={'timeout': 60}` 參數
   - 60秒超時限制，避免無限等待

2. **自動重試機制**
   - `max_retries=2`：最多重試 2 次
   - 超時後等待 2s, 4s 再重試
   - 速率限制後等待 5s 再重試

3. **增強錯誤處理**
   - 特定識別 `timeout` 錯誤
   - 特定識別 `rate limit` (429) 錯誤
   - 特定識別 `safety filter` 錯誤
   - 更詳細的錯誤訊息輸出

4. **回應驗證**
   - 檢查回應是否為空
   - 避免空回應導致後續錯誤

---

### 2. 修復 favicon.ico 404

檔案: `templates/index.html` (已在之前創建)

在 `<head>` 中添加：

```html
<link rel="icon" type="image/png" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==">
```

這是一個 1x1 透明 PNG 圖像，避免 404 錯誤。

---

### 3. AI 聊天室介面集成

#### 3.1 前端介面 (`templates/index.html`)

在分析結果下方添加：

```html
<!-- AI 聊天室 Panel -->
<div class="card mt-4" id="ai-chat-panel" style="display: none;">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5>🤖 AI 分析詳細 - 聊天室風格</h5>
        <button class="btn btn-sm btn-outline-secondary" onclick="toggleAIChatPanel()">
            收起/展開
        </button>
    </div>
    <div class="card-body" id="ai-chat-content">
        <!-- AI 聊天室內容 -->
    </div>
</div>
```

#### 3.2 JavaScript 邏輯 (`static/js/ai_chat.js`)

主要功能：
- 自動加載 AI 分析數據
- 渲染所有模型回應 (Model A, Model B, Arbitrator, Executor)
- 顯示 Prompt 資訊
- 顯示最終決策摘要
- 每 30 秒自動更新

#### 3.3 API 路由 (`api_routes_ai_chat.py`)

已存在的檔案，不需修改。提供：
- `/api/ai-chat-data` - 獲取最新 AI 分析數據
- `/api/ai-chat/history` - 獲取歷史分析記錄

---

## 使用方法

### 1. 更新代碼

```bash
git pull origin main
```

### 2. 重啟 Flask 伺服器

```bash
python app_flask.py
```

### 3. 測試 AI 分析

1. 打開 http://localhost:5000
2. 配置 API Key (如果還沒有)
3. 點擊「獲取實時訊號」按鈕
4. 等待 2-3 秒，AI 聊天室 Panel 會自動顯示
5. 檢查 Gemini_Flash_B1 是否正常分析

---

## 預期結果

### 修復前
```
[Llama_70B_A1] 分析中...
[OK] [Llama_70B_A1]: OPEN_LONG (信心度 60%) - 2.7s

[Gemini_Flash_B1] 分析中...
(卡住，無回應)
```

### 修復後
```
[Llama_70B_A1] 分析中...
[OK] [Llama_70B_A1]: OPEN_LONG (信心度 60%) - 2.7s

[Gemini_Flash_B1] 分析中...
[OK] [Gemini_Flash_B1]: HOLD (信心度 55%) - 3.2s
     理由: 市場趋勢不明朗...

[仲裁者] 調用中...
[OK] 仲裁完成: OPEN_LONG (信心 65%) - 2.1s

[Executor] 審核中...
[OK] EXECUTE - 信心度足夠
```

---

## 技術細節

### Gemini API 超時設置

```python
response = model.generate_content(
    full_prompt,
    generation_config=genai.GenerationConfig(
        temperature=0.2,
        max_output_tokens=4000
    ),
    request_options={'timeout': 60}  # 超時設置
)
```

### 重試邏輯

```python
for attempt in range(max_retries):
    try:
        # ... API 調用 ...
    except Exception as api_error:
        if 'timeout' in str(api_error).lower():
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"[RETRY] 超時，{wait_time}秒後重試...")
                time.sleep(wait_time)
                continue
```

---

## 已知限制

1. **Gemini API 速率限制**
   - 免費版本有每分鐘 15 次請求限制
   - 如果觸發限制，會自動切換到備用模型 (Llama 70B 或 Mixtral 8x7B)

2. **超時時間**
   - 預設 60 秒超時
   - 如果網路狀況不佳，可能需要調高

3. **聊天室儲存**
   - 只儲存最新一次分析的完整資訊
   - 歷史記錄不包含完整 Prompt 和模型回應

---

## 後續優化建議

1. **增加模型切換 UI**
   - 讓用戶可以在 Web 介面手動切換主力/備用模型
   
2. **優化聊天室呈現**
   - 添加 Markdown 渲染
   - 添加語法高亮 (JSON)
   - 支持複製 Prompt/回應

3. **儲存分析歷史**
   - 儲存每次分析的完整 Prompt 和回應
   - 支持按時間/符號篩選
   - 支持導出 CSV/JSON

4. **增加效能監控**
   - 每個模型的平均回應時間
   - 成功率/失敗率統計
   - API 費用估算

---

## 故障排除

### Gemini API 仍然卡住

1. 檢查 API Key 是否有效
```bash
echo $GOOGLE_API_KEY
```

2. 檢查網路連接
```bash
ping -c 4 generativelanguage.googleapis.com
```

3. 查看詳細錯誤訊息
```bash
tail -f nohup.out  # 如果使用 nohup 啟動
```

4. 嘗試手動測試
```python
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

try:
    response = model.generate_content(
        "Test",
        request_options={'timeout': 10}
    )
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
```

### favicon.ico 仍然 404

確保 `templates/index.html` 已更新並包含：
```html
<link rel="icon" type="image/png" href="data:image/png;base64,...">
```

清除瀏覽器快取：
- Chrome: Ctrl+Shift+Delete
- Firefox: Ctrl+Shift+Delete

### AI 聊天室不顯示

1. 檢查 `/api/ai-chat-data` 是否有回應
```bash
curl http://localhost:5000/api/ai-chat-data
```

2. 查看瀏覽器控制台錯誤
```
F12 -> Console
```

3. 確保已執行分析
   - 點擊「獲取實時訊號」
   - 等待 2-3 秒

---

## 聯繫資訊

如果遇到問題，請提供：
1. 完整的錯誤訊息
2. `app_flask.py` 的輸出日誌
3. 瀏覽器控制台的錯誤訊息
4. Python 版本和已安裝的套件版本

---

## 更新記錄

- **2026-03-07**: 初始版本
  - 修復 Gemini API 超時問題
  - 修復 favicon.ico 404
  - 添加 AI 聊天室介面
