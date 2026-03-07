# ⚡ 雙模型快速開始

## ✅ 更新完成

你的系統現在已經集成了**雙模型決策系統**！

---

## 🚀 啟動步驟

### 1️⃣ 更新代碼

```bash
cd STW
git pull origin main
```

### 2️⃣ 啟動 Flask

```bash
python app_flask.py
```

你應該看到：

```
============================================================
  Flask Server Starting - STW AI Trading System
============================================================
  Access at: http://localhost:5000
  Features:
    - Real-time market data from Binance API
    - WebSocket live updates
    - Auto AI prediction logging
    - Config auto-save & restore
    - Encrypted API keys storage
    - Multi-API management
    - Learning cases library
    - Module-level loading (no page refresh)
    - Multi-tab simultaneous operation
    - Dual-model decision system (NEW!)
      Mode: consensus
      Enabled: False
============================================================
  Config Manager: Enabled
  Dual Model: Enabled
============================================================
```

### 3️⃣ 配置 API Keys

打開 http://localhost:5000 → 點擊「設定」

配置至少 **2 個 API Key**（用於雙模型）：

#### 推薦組合：

**Option 1: Groq + OpenRouter** (免費且穩定)
- **Groq API Key**: [console.groq.com/keys](https://console.groq.com/keys)
- **OpenRouter API Key**: [openrouter.ai/keys](https://openrouter.ai/keys)

**Option 2: Groq + Google Gemini** (免費且質量好)
- **Groq API Key**: [console.groq.com/keys](https://console.groq.com/keys)
- **Google API Key**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

## 🎮 啟用雙模型

### 方法 1: 透過配置文件 (推薦)

在系統設定頁面添加：

```json
{
  "use_dual_model": true,
  "dual_model_mode": "consensus"
}
```

**模式選擇**：
- `"consensus"` - 共識模式（最安全，推薦）
- `"vote"` - 投票模式（與 consensus 相同）
- `"weighted"` - 加權模式（更激進）

### 方法 2: 修改 config.json

直接編輯 `config.json`：

```json
{
  "GROQ_API_KEY": "gsk_...",
  "OPENROUTER_API_KEY": "sk-or-v1-...",
  "use_dual_model": true,
  "dual_model_mode": "consensus"
}
```

然後重啟 Flask。

---

## 📊 使用效果

### 單模型輸出

```bash
[ANALYZE] Latest price: $69,543.21
[ANALYZE] Model type: single

AI 預測已記錄: OPEN_LONG (信心度 75%)
```

### 雙模型輸出

```bash
============================================================
🔍 雙模型決策系統啟動
============================================================

🤖 Model A (DeepSeek-R1) 分析中...
✅ 使用 API: Groq_R1_Distill (deepseek-r1-distill-llama-70b)
✅ AI 分析成功: OPEN_LONG (信心度 82%)

🤖 Model B (備用模型) 分析中...
✅ 使用 API: OpenRouter_R1 (deepseek/deepseek-r1:free)
✅ AI 分析成功: OPEN_LONG (信心度 78%)

============================================================
⚡ 決策比對
============================================================
Model A: OPEN_LONG (信心度 82%)
  理由: RSI 超賣 + MACD 金叉

Model B: OPEN_LONG (信心度 78%)
  理由: 布林帶下軌反彈

============================================================
✅ 最終決策
============================================================
Action: OPEN_LONG
Confidence: 80%
Reasoning: ✅ 兩個模型一致建議: OPEN_LONG
============================================================

[ANALYZE] Latest price: $69,543.21
[ANALYZE] Model type: dual

AI 預測已記錄: OPEN_LONG (信心度 80%) (dual model)
```

---

## 📈 查看統計

### API 請求

```bash
curl http://localhost:5000/api/dual-model/stats
```

**輸出示例**：

```json
{
  "enabled": true,
  "mode": "consensus",
  "performance": {
    "total_decisions": 45,
    "agreements": 38,
    "disagreements": 7,
    "agreement_rate": 84.4
  },
  "recent_agreement_rate": 90.0
}
```

---

## 🔄 切換模式

### 關閉雙模型

修改 `config.json`：

```json
{
  "use_dual_model": false
}
```

重啟後會自動回到單模型。

### 更改模式

```json
{
  "use_dual_model": true,
  "dual_model_mode": "weighted"  // 改為加權模式
}
```

---

## ⚙️ 三種模式對比

| 模式 | 一致時 | 不一致時 | 適用場景 |
|------|--------|---------|----------|
| **Consensus** | 執行 | 強制 HOLD | 保守交易，追求高勝率 |
| **Vote** | 執行 | HOLD | 與 Consensus 相同 (2 模型) |
| **Weighted** | 執行 | 選信心度高的 × 70% | 積極交易，不错過機會 |

---

## ✅ 優勢

1. **更高準確性** - 兩個模型互相驗證
2. **降低風險** - 意見不一致時保守策略
3. **提高信心** - 共識決策更可靠
4. **多角度分析** - 不同 API 的推理角度
5. **數據驗證** - 追蹤一致率統計

---

## ⚠️ 注意事項

- **速度**: 雙模型需要 2 次 API 調用，時間約 2 倍（4-6 秒）
- **額度**: 每次決策消耗 2 個 API 請求
- **成本**: 如果使用付費 API，成本翻倍

建議：
- 低頻交易（< 10 次/天）→ 使用 **Consensus**
- 中頻交易（10-50 次/天）→ 使用 **Consensus** 或 **Vote**
- 高頻交易（> 50 次/天）→ 使用 **Weighted** 或關閉雙模型

---

## 📝 日誌示例

雙模型的決策日誌會自動標記：

```json
{
  "timestamp": "2026-03-07 11:30:00",
  "action": "OPEN_LONG",
  "confidence": 80,
  "model_type": "dual",
  "agreement": true,
  "reasoning": "✅ 兩個模型一致建議: OPEN_LONG..."
}
```

---

## 🤔 常見問題

### Q1: 為什麼雙模型沒有啟動？

檢查：
1. `config.json` 中 `use_dual_model: true`
2. 至少配置 2 個 API Key
3. 重啟 Flask

### Q2: 兩個模型使用相同 API 嗎？

不會。`MultiAPIManager` 會自動輪轉使用不同的 API 提供商。

### Q3: 如何知道一致率？

```bash
curl http://localhost:5000/api/dual-model/stats
```

或查看終端輸出的統計資訊。

### Q4: 可以使用 3 個模型嗎？

目前僅支持 2 個模型。如果需要 3+，可修改 `dual_model_agent.py`。

---

## 🎉 完成！

現在你已經拇有了：

✅ 雙模型決策系統
✅ 3 種決策模式可選
✅ 多 API 自動輪轉
✅ 一致率統計追蹤
✅ 完整日誌記錄

開始交易吧！🚀
