# ✅ 如何啟用兩階段仲裁？

## 🎯 3 步驟完成

### 1️⃣ 更新代碼

```bash
git pull origin main
python app_flask.py
```

### 2️⃣ 網頁設定

1. 打開網頁: `http://localhost:5000`
2. 點擊 **「設定」** 分頁
3. 在 **「兩階段仲裁決策」** 區塊，**打開** 開關
4. 填入至少 2 個 API Keys：
   - Groq API Key
   - Google API Key
   - OpenRouter API Key (選填)

5. 點擊 **「保存設定」**

### 3️⃣ 驗證

點擊 **「獲取實時訊號」**，你會看到：

```
┌────────────────────────┐
│  🧠 兩階段仲裁決策  │
├────────┬───────────────┤
│ Model A │ Model B      │
│ Groq    │ Google Gemini│
└────────┴───────────────┘
```

---

## 🔑 獲取 API Keys

### Groq (最快，額度最高)
1. 去 https://console.groq.com
2. 註冊帳號
3. 建立 API Key
4. 免費: 14,400 次/天

### Google Gemini (推理最強)
1. 去 https://aistudio.google.com
2. 建立 API Key
3. 免費: 1,500 次/天

### OpenRouter (備用)
1. 去 https://openrouter.ai
2. 註冊帳號
3. 免費: 200 次/天 (多種模型)

---

## ❓ 常見問題

### Q: 為什麼還是單模型？

A: 確認以下三點：
1. 網頁設定中有打開「兩階段仲裁決策」開關
2. 至少填入 2 個 API Keys
3. 點擊「保存設定」後**重新點擊 AI 分析**

### Q: API 額度用完了？

A: 系統會自動切換到備用 API。建議：
- 同時配置 Groq + Google + OpenRouter
- 這樣每天有 16,100 次額度

### Q: 兩階段仲裁會更慢嗎？

A: 
- **共識**: 2 秒 (2 個模型並行)
- **分歧需仲裁**: 3 秒 (再調用第 3 個模型)
- 一般 80% 情況都能達成共識，不需仲裁

---

## 👍 完成！

你現在可以使用兩階段仲裁決策系統了！

網頁會顯示：
- 🤖 Model A 的分析結果
- 🤖 Model B 的分析結果
- ✅/⚠️ 是否達成共識
- 🧠 Arbitrator 的仲裁 (如果需要)
- ✅ 最終決策
