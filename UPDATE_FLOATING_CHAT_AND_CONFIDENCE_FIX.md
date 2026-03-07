# 懸浮球聊天室 & 信心度修復

## 更新時間
2026-03-07 21:57 CST

## 更新內容

### 1. ✅ 修復信心度顯示為 0% 的問題

**問題**:
- 三階段仲裁後，網頁顯示信心度為 0%
- 實際 Log 顯示是 55%

**原因**:
- `decision.confidence` 是原始信心度
- 但三階段審核後，調整後的信心度儲存在 `decision.adjusted_confidence`
- 前端 `main.js` 只讀取 `decision.confidence`

**修復**:
```javascript
// 修復前
const confidence = decision.confidence || 0;

// 修復後
const confidence = decision.adjusted_confidence !== undefined ? 
                   decision.adjusted_confidence : 
                   (decision.confidence || 0);
```

**測試**:
```bash
# 1. 更新代碼
git pull origin main

# 2. 重啟伺服器
pkill -f app_flask.py
python app_flask.py

# 3. 點擊「獲取實時訊號」
# 4. 檢查信心度是否正常顯示
```

---

### 2. ✨ 懸浮球聊天室功能

**功能介紹**:
- 在網頁右下角顯示一個圓形懸浮球按鈕
- 點擊後打開聊天室視窗，不用另開新分頁
- 顯示所有 AI 模型的完整回應
- 美觀的開啟動畫效果
- 與網頁整體風格一致

**視覺設計**:
```
網頁主體
├── 左側選單
├── 主內容區
└── 右下角
    └── 🗨️ 懸浮球按鈕 (紫色漸層)
        └── 點擊後彈出聊天室視窗
```

**特性**:
1. ✅ 懸浮球按鈕
   - 大小: 64x64px
   - 位置: 右下角 (bottom: 32px, right: 32px)
   - 游層: 紫色漸層 (#667eea -> #764ba2)
   - 效果: Hover 放大 1.1x，Shadow 加深
   - 通知點: 紅色閃爍提示新訊息

2. ✅ 聊天室視窗
   - 大小: 420x600px
   - 位置: 懸浮球上方
   - 背景: 半透明毛玻璃效果
   - 動畫: 縮放 + 淡入 (0.3s cubic-bezier)
   - 標題欄: 紫色漸層
   - 按鈕: 最小化 + 關閉

3. ✅ 訊息氣泡
   - 用戶 Prompt: 藍綠色氣泡 (右側)
   - Model A: 藍色氣泡 (左側)
   - Model B: 綠色氣泡 (左側)
   - Arbitrator: 紫色氣泡 (左側)
   - Executor: 橙色氣泡 (左側)
   - 最終決策: 綠色高亮框

4. ✅ 自動更新
   - 點擊「獲取實時訊號」後自動更新
   - 如果聊天室關閉，顯示通知點
   - 如果聊天室打開，直接更新內容

**檔案結構**:
```
STW/
├── static/
│   ├── css/
│   │   └── floating_chat.css       (新增 - 7.8KB)
│   ├── js/
│   │   ├── main.js                  (修改 - 信心度修復)
│   │   └── floating_chat.js         (新增 - 11.8KB)
└── templates/
    └── index.html                   (修改 - 引入懸浮球)
```

---

## 使用指南

### 1. 更新代碼
```bash
cd ~/STW
git pull origin main
```

### 2. 確認新檔案
```bash
ls static/css/floating_chat.css
# 應該存在

ls static/js/floating_chat.js
# 應該存在
```

### 3. 重啟伺服器
```bash
pkill -f app_flask.py
python app_flask.py
```

### 4. 測試懸浮球聊天室

**步驟 1: 打開網頁**
```
http://localhost:5000
```

**步驟 2: 查看懸浮球**
- ✅ 右下角有一個紫色圓形按鈕
- ✅ Hover 時會放大
- ✅ 有 Shadow 效果

**步驟 3: 點擊「獲取實時訊號」**
- ✅ AI 分析完成
- ✅ 信心度正常顯示 (不是 0%)
- ✅ 懸浮球出現紅色通知點

**步驟 4: 點擊懸浮球**
- ✅ 聊天室視窗彈出
- ✅ 有縮放 + 淡入動畫
- ✅ 顯示所有 AI 模型回應

**步驟 5: 檢查聊天室內容**
- ✅ 用戶 Prompt (藍綠色，右側)
- ✅ Model A 回應 (藍色，左側)
- ✅ Model B 回應 (綠色，左側)
- ✅ Arbitrator 回應 (紫色，左側)
- ✅ Executor 審核 (橙色，左側)
- ✅ 最終決策 (綠色高亮)

**步驟 6: 測試按鈕**
- ✅ 最小化按鈕: 收起視窗
- ✅ 關閉按鈕: 關閉視窗
- ✅ 再次點擊懸浮球: 重新打開

---

## 技術細節

### CSS 關鍵樣式

**1. 懸浮球按鈕**
```css
.floating-chat-button {
    position: fixed;
    bottom: 32px;
    right: 32px;
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.floating-chat-button:hover {
    transform: scale(1.1);
    box-shadow: 0 12px 32px rgba(102, 126, 234, 0.6);
}
```

**2. 聊天室視窗**
```css
.floating-chat-window {
    position: fixed;
    bottom: 110px;
    right: 32px;
    width: 420px;
    height: 600px;
    background: rgba(20, 30, 50, 0.98);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
    transform: translateY(20px) scale(0.9);
    opacity: 0;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.floating-chat-window.open {
    transform: translateY(0) scale(1);
    opacity: 1;
}
```

**3. 通知點動畫**
```css
.notification-dot {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 14px;
    height: 14px;
    background: #ff4757;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.2); opacity: 0.8; }
}
```

### JavaScript 關鍵邏輯

**1. 初始化**
```javascript
function init() {
    const button = createFloatingButton();
    const chatWindow = createChatWindow();
    
    // 懸浮球點擊事件
    button.addEventListener('click', () => {
        if (isOpen) {
            closeChatWindow();
        } else {
            openChatWindow();
        }
    });
    
    // 監聽 AI 分析完成事件
    window.addEventListener('aiAnalysisComplete', () => {
        if (!isOpen) {
            // 顯示通知點
            showNotificationDot();
        } else {
            // 自動更新
            loadChatData();
        }
    });
}
```

**2. 渲染訊息**
```javascript
function renderChatMessages(data) {
    // 用戶 Prompt
    if (data.prompt_info) {
        html += renderUserPrompt(data.prompt_info);
    }
    
    // 每個模型回應
    data.models.forEach(model => {
        html += renderModelResponse(model);
    });
    
    // 最終決策
    if (data.final_decision) {
        html += renderFinalDecision(data.final_decision);
    }
    
    messagesContainer.innerHTML = html;
    scrollToBottom();
}
```

**3. 事件觸發**
```javascript
// 在 main.js 中，AI 分析完成後觸發
async function analyzeMarket() {
    // ... AI 分析邏輯 ...
    
    // 觸發事件
    window.dispatchEvent(new CustomEvent('aiAnalysisComplete'));
}
```

---

## 響應式設計

### 手機版 (寬度 < 768px)
```css
@media (max-width: 768px) {
    .floating-chat-button {
        width: 56px;
        height: 56px;
        bottom: 24px;
        right: 24px;
    }
    
    .floating-chat-window {
        width: calc(100vw - 32px);
        height: calc(100vh - 120px);
        bottom: 90px;
        right: 16px;
    }
}
```

---

## 故障排除

### 問題 1: 懸浮球不顯示

**原因**: CSS/JS 檔案未加載

**解決**:
```bash
# 檢查檔案是否存在
ls static/css/floating_chat.css
ls static/js/floating_chat.js

# 檢查 index.html 是否引入
grep "floating_chat" templates/index.html

# 重啟伺服器
pkill -f app_flask.py
python app_flask.py
```

### 問題 2: 聊天室空白

**原因**: AI 分析完成事件未觸發

**解決**:
```bash
# 檢查 main.js 是否有觸發事件
grep "aiAnalysisComplete" static/js/main.js

# 應該看到:
window.dispatchEvent(new CustomEvent('aiAnalysisComplete'));
```

### 問題 3: 信心度仍為 0%

**原因**: main.js 未更新或 Python 快取

**解決**:
```bash
# 1. 確認 main.js 有修復
grep "adjusted_confidence" static/js/main.js

# 應該看到:
const confidence = decision.adjusted_confidence !== undefined

# 2. 清除瀏覽器快取
Ctrl+Shift+R (強制重新加載)

# 3. 檢查開發者工具 Console
# 是否有 JS 錯誤
```

### 問題 4: 動畫不流暢

**原因**: 瀏覽器不支持或減少動畫模式

**解決**:
```css
/* 已在 CSS 中處理 */
@media (prefers-reduced-motion: reduce) {
    .floating-chat-button,
    .floating-chat-window,
    .chat-message {
        animation: none;
        transition: none;
    }
}
```

---

## 未來優化

1. **添加聊天記錄**
   - 保存最近 10 次 AI 分析結果
   - 可以切換查看歷史分析

2. **添加搜索功能**
   - 搜索特定模型的回應
   - 過濾不同時間段的分析

3. **添加匯出功能**
   - 匯出聊天記錄為 Markdown
   - 匯出為 PDF 報告

4. **添加語音通知**
   - AI 分析完成時發出提示音
   - 可在設定中關閉

5. **添加快捷鍵**
   - Ctrl+K: 打開/關閉聊天室
   - Esc: 關閉聊天室

---

## 總結

✅ **信心度問題已修復**
- 優先顯示 `adjusted_confidence`
- 三階段審核後的信心度正常顯示

✨ **懸浮球聊天室已完成**
- 美觀的 UI 設計
- 流暢的動畫效果
- 完整的功能實現
- 與網頁風格一致

🚀 **使用體驗提升**
- 不用另開分頁查看 AI 分析
- 所有資訊集中在一個視窗
- 隨時查看，不影響主頁面操作

---

## 相關文檔

- [REFACTORING_MODULAR_ARCHITECTURE.md](./REFACTORING_MODULAR_ARCHITECTURE.md) - 模塊化重構
- [BUGFIX_GEMINI_AND_AI_CHAT.md](./BUGFIX_GEMINI_AND_AI_CHAT.md) - Gemini API 修復
- [UPDATE_LINE_CHAT_AND_SYMBOL_FIX.md](./UPDATE_LINE_CHAT_AND_SYMBOL_FIX.md) - LINE 聊天室
- [UPDATE_FLOATING_CHAT_AND_CONFIDENCE_FIX.md](./UPDATE_FLOATING_CHAT_AND_CONFIDENCE_FIX.md) - 本文檔

---

如有任何問題，請提供詳細的錯誤訊息和開發者工具 Console 輸出。
