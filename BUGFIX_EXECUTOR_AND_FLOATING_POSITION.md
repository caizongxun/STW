# Executor 日誌 & 懸浮球位置修復

## 更新時間
2026-03-07 22:13 CST

## 問題 1: Executor JSON 解析失敗日誌被截斷

### 問題描述
```
[ERROR] 解析失敗 - AI 審核員完整回應:
======================================================================
作為一名經驗豐富的加密貨幣交易員，我將對 AI 仲裁者的決策進行最終審核。

**審核分析：**

1.  **AI 決策概述：**
    *   **行動：** 開啓多頭 (OPEN_LONG)
    *   **信心度：** 70%
    *   **
======================================================================

[AI REVIEW] REJECT
            拒絕執行: 解析失敗...
```

### 原因
- `print()` 函數有輸出長度限制
- AI 回應可能超過 1000 字，被截斷

### 修復

**修改檔案**: `core/trading_executor_agent.py`

```python
# 修復前
print(raw_content)

# 修復後 - 分段打印
for i in range(0, len(raw_content), 500):
    print(raw_content[i:i+500])
```

**Commit**: [05aacda](https://github.com/caizongxun/STW/commit/05aacda9054bba84a411fcf7baad9f24f65e3bb7)

---

## 問題 2: 懸浮球出現在左下角而非右下角

### 問題描述
懸浮球按鈕出現在畫面左下角，而不是預期的右下角。

### 可能原因

1. **CSS 樣式衝突**
   - 其他 CSS 檔案覆盖了 `right` 屬性
   - 可能有全局 `left` 設定

2. **瀏覽器快取**
   - CSS 檔案被快取，未加載最新版本

3. **JavaScript 動態設定**
   - floating_chat.js 中可能有動態設定位置

### 診斷步驟

**1. 檢查瀏覽器開發者工具**
```
F12 打開開發者工具
選擇 Elements 頁籤
點擊懸浮球元素
查看 Computed 樣式
檢查 right 和 left 的實際值
```

**2. 檢查 CSS 檔案**
```css
/* static/css/floating_chat.css */
.floating-chat-button {
    position: fixed;
    bottom: 32px;
    right: 32px;  /* 應該是 right */
    left: auto;   /* left 應該是 auto */
}
```

**3. 檢查 JavaScript**
```bash
grep -n "left" static/js/floating_chat.js
grep -n "right" static/js/floating_chat.js
```

### 解決方案

#### 方案 1: 強制重新加載

```bash
# 在瀏覽器中
Ctrl+Shift+R  # Windows/Linux
Cmd+Shift+R   # Mac
```

#### 方案 2: 清除快取

```bash
# 重啟 Flask 伺服器
pkill -f app_flask.py
python app_flask.py

# 瀏覽器中清除快取
F12 -> Application -> Clear Storage -> Clear site data
```

#### 方案 3: 手動修正 CSS

如果以上方法無效，在 `floating_chat.css` 中加入 `!important`：

```css
.floating-chat-button {
    position: fixed !important;
    bottom: 32px !important;
    right: 32px !important;
    left: auto !important;
    width: 64px;
    height: 64px;
    /* ... */
}

.floating-chat-window {
    position: fixed !important;
    bottom: 110px !important;
    right: 32px !important;
    left: auto !important;
    /* ... */
}
```

#### 方案 4: 檢查其他 CSS 檔案

```bash
# 搜尋所有 CSS 中的 .floating-chat-button
grep -r "floating-chat-button" static/css/

# 檢查是否有覆盖
grep -A 10 "floating-chat-button" static/css/*.css
```

---

## 測試步驟

### 1. 更新代碼
```bash
cd ~/STW
git pull origin main
```

### 2. 重啟伺服器
```bash
pkill -f app_flask.py
python app_flask.py
```

### 3. 測試 Executor 日誌

**步驟**:
1. 訪問 http://localhost:5000
2. 點擊「獲取實時訊號」
3. 如果 Executor 解析失敗，查看 Console 輸出

**預期結果**:
```
[ERROR] 解析失敗 - AI 審核員完整回應:
======================================================================
作為一名經驗豐富的加密貨幣交易員...
(完整內容，每 500 字一段)
...
======================================================================
```

### 4. 測試懸浮球位置

**步驟**:
1. 訪問 http://localhost:5000
2. 查看懸浮球按鈕位置
3. F12 打開開發者工具
4. 選擇 Elements
5. 點擊懸浮球
6. 查看 Computed 樣式

**預期結果**:
- `position`: fixed
- `bottom`: 32px
- `right`: 32px
- `left`: auto

**如果 left 不是 auto**:
```javascript
// 在 Console 中執行
document.querySelector('.floating-chat-button').style.left = 'auto';
document.querySelector('.floating-chat-button').style.right = '32px';
```

---

## 故障排除

### 問題: Executor 仍然解析失敗

**原因**: Gemini 模型輸出格式不一致

**解決**:

1. 檢查強健解析器是否啟用
```python
# core/trading_executor_agent.py
if HAS_ROBUST_PARSER:
    print("[OK] 執行審核員使用強健 JSON 解析器")
```

2. 檢查 `core/json_parser_robust.py` 是否存在
```bash
ls -la core/json_parser_robust.py
```

3. 如果不存在，手動解析 AI 回應
```bash
# 查看完整日誌
grep -A 100 "AI 審核員完整回應" logs/*.log
```

### 問題: 懸浮球位置無法修正

**原因**: JavaScript 動態設定了位置

**解決**:

1. 檢查 `floating_chat.js` 中是否有 `style.left` 設定
```bash
grep -n "style.left" static/js/floating_chat.js
grep -n "style.right" static/js/floating_chat.js
```

2. 如果發現，將 `left` 改為 `right`
```javascript
// 修改前
button.style.left = '32px';

// 修改後
button.style.right = '32px';
button.style.left = 'auto';
```

3. 重啟伺服器並強制重新加載

---

## 相關文檔

- [UPDATE_FLOATING_CHAT_AND_CONFIDENCE_FIX.md](./UPDATE_FLOATING_CHAT_AND_CONFIDENCE_FIX.md) - 懸浮球聊天室功能
- [BUGFIX_GEMINI_AND_AI_CHAT.md](./BUGFIX_GEMINI_AND_AI_CHAT.md) - Gemini API 修復
- [BUGFIX_EXECUTOR_AND_FLOATING_POSITION.md](./BUGFIX_EXECUTOR_AND_FLOATING_POSITION.md) - 本文檔

---

## 總結

✅ **Executor 日誌已改進**
- 分段打印，每 500 字一段
- 不再被截斷
- 可以查看完整 AI 回應

🔍 **懸浮球位置排查**
- CSS 樣式已確認正確
- 需要檢查瀏覽器快取
- 需要檢查 JavaScript 動態設定

👉 **下一步**
1. `git pull origin main`
2. `pkill -f app_flask.py && python app_flask.py`
3. Ctrl+Shift+R 強制重新加載瀏覽器
4. F12 檢查懸浮球元素位置
5. 如果位置錯誤，在 Console 手動修正

---

如有問題，請提供：
1. 開發者工具 Console 輸出
2. 懸浮球元素的 Computed 樣式截圖
3. `floating_chat.js` 中與位置相關的代碼
