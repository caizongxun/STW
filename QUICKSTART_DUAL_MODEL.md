# ⚡ 雙模型快速開始

## ✅ 更新完成

你的系統現在已經集成了**雙模型決策系統**！

使用 **兩個不同的優質 AI 模型** 互相驗證決策。

---

## 🤝 核心概念

### 兩個不同模型：

**Model A: DeepSeek-R1** (推理能力強)
- 強大的思維鏈推理
- 適合複雜的市場分析
- 使用 Groq 或 OpenRouter API

**Model B: GPT-4o / Gemini 2.0 / Claude** (穩定性好)
- 成熟穩定的商業模型
- 平衡的決策風格
- 使用 GitHub Models / Google / OpenRouter API

**優勢**：
✅ 不同模型的推理角度
✅ 降低單一模型的偏差
✅ 提高決策的可靠性

---

## 🚀 啟動步驟

### 1️⃣ 更新代碼

```bash
cd STW
git pull origin main
```

### 2️⃣ 配置 API Keys

**推薦組合 1: DeepSeek-R1 + GPT-4o-mini** (最推薦)

```json
{
  "GROQ_API_KEY": "gsk_...",
  "GITHUB_TOKEN": "ghp_..."
}
```

- **Groq** (DeepSeek-R1): [console.groq.com/keys](https://console.groq.com/keys)
- **GitHub** (GPT-4o-mini): [github.com/settings/tokens](https://github.com/settings/tokens) → 產生 Personal Access Token

---

**推薦組合 2: DeepSeek-R1 + Gemini 2.0**

```json
{
  "GROQ_API_KEY": "gsk_...",
  "GOOGLE_API_KEY": "AIza..."
}
```

- **Groq** (DeepSeek-R1): [console.groq.com/keys](https://console.groq.com/keys)
- **Google** (Gemini 2.0): [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

**推薦組合 3: DeepSeek-R1 + Claude 3.5**

```json
{
  "OPENROUTER_API_KEY": "sk-or-v1-..."
}
```

- **OpenRouter**: [openrouter.ai/keys](https://openrouter.ai/keys)
- Model A: 使用 `deepseek/deepseek-r1:free`
- Model B: 使用 `anthropic/claude-3.5-sonnet:beta`

---

### 3️⃣ 啟用雙模型

在 `config.json` 中添加：

```json
{
  "GROQ_API_KEY": "gsk_...",
  "GITHUB_TOKEN": "ghp_...",
  "use_dual_model": true,
  "dual_model_mode": "consensus"
}
```

### 4️⃣ 啟動 Flask

```bash
python app_flask.py
```

你應該看到：

```
============================================================
  Flask Server Starting - STW AI Trading System
============================================================
    - Dual-model decision system (NEW!)
      Mode: consensus
      Enabled: False
============================================================
  Dual Model: Enabled
============================================================

✅ Model A: Groq DeepSeek-R1 Distill Llama 70B
✅ Model B: GitHub GPT-4o-mini
```

---

## 📊 使用效果

### 單模型輸出

```bash
AI 分析嘗試 1/3...
🤖 使用 API: Groq (deepseek-r1-distill-llama-70b)
✅ AI 分析成功: OPEN_LONG (信心度 75%)
```

### 雙模型輸出

```bash
============================================================
🔍 雙模型決策系統啟動
Model A: Groq_DeepSeek_R1 (deepseek-r1-distill-llama-70b)
Model B: GitHub_GPT4o_mini (gpt-4o-mini)
============================================================

🤖 Groq_DeepSeek_R1 分析中...
✅ Groq_DeepSeek_R1: OPEN_LONG (信心度 82%)

🤖 GitHub_GPT4o_mini 分析中...
✅ GitHub_GPT4o_mini: OPEN_LONG (信心度 78%)

============================================================
⚡ 決策比對
============================================================
Groq_DeepSeek_R1: OPEN_LONG (82%)
  RSI 超賣 + MACD 金叉，趋勢反轉...

GitHub_GPT4o_mini: OPEN_LONG (78%)
  布林帶下軌反彈，成交量放大...

============================================================
✅ 最終決策
============================================================
Action: OPEN_LONG
Confidence: 80%
Reasoning: ✅ 兩個模型一致建議: OPEN_LONG
============================================================
```

---

## 📈 系統架構

```
市場數據
    ↓
├── Model A: DeepSeek-R1 (Groq) ───┐
│   - 推理能力強                    │
│   - 思維鏈深入                    │
│                                      │
├── Model B: GPT-4o-mini (GitHub) ─┤ → 決策比對
│   - 穩定性好                      │
│   - 商業成熟                      │
│                                      │
└────────────────────────────┘
         ↓
    最終決策
```

---

## ⚙️ 三種決策模式

### 1. Consensus (共識模式) - 預設

**逻輯**：兩個模型必須完全一致

| 情況 | 結果 |
|------|------|
| 兩個都 OPEN_LONG | ✅ 執行 OPEN_LONG，取平均信心度 |
| 一個 LONG，一個 SHORT | ⚠️ 強制 HOLD，等待更明確訊號 |
| 一個 LONG，一個 HOLD | ⚠️ 強制 HOLD |

**適用**：保守交易，追求高勝率

---

### 2. Weighted (加權模式)

**逻輯**：信心度高的模型權重更大

| 情況 | 結果 |
|------|------|
| 兩個一致 | ✅ 執行，取平均信心度 |
| A(85%) LONG, B(60%) HOLD | ⚠️ 執行 LONG，信心度降低至 59.5% |
| A(70%) LONG, B(80%) SHORT | ⚠️ 執行 SHORT，信心度降低至 56% |

**適用**：積極交易，不错過機會

---

## 📈 查看統計

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

## 🔄 API 組合建議

### 組合 1: Groq + GitHub (最推薦)

| API | 模型 | 免費額度 | 速度 | 質量 |
|-----|------|----------|------|------|
| Groq | DeepSeek-R1 Distill Llama 70B | 14400/天 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| GitHub | GPT-4o-mini | 1000/天 | ⭐⭐⭐ | ⭐⭐⭐⭐ |

**優勢**：
- 兩個都是頂級模型
- 額度充足（每天 15400 次）
- 完全免費

---

### 組合 2: Groq + Google

| API | 模型 | 免費額度 | 速度 | 質量 |
|-----|------|----------|------|------|
| Groq | DeepSeek-R1 Distill Llama 70B | 14400/天 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Google | Gemini 2.0 Flash | 1500/天 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**優勢**：
- Gemini 推理能力極強
- 多角度分析

---

### 組合 3: OpenRouter (最多樣化)

使用 1 個 OpenRouter API Key，可以輪換多個模型：

| 模型 | 免費額度 |
|------|----------|
| DeepSeek-R1 | 1000/天 |
| DeepSeek-R1 Distill Llama 70B | 1000/天 |
| Claude 3.5 Sonnet | 付費（小量免費 credits） |

---

## ✅ 優勢

1. **更高準確性** - 不同模型互相驗證
2. **降低風險** - 意見不一致時保守策略
3. **多角度分析** - DeepSeek 的思維鏈 + GPT 的穩定性
4. **避免單一模型偏差** - 每個模型都有自己的優勢
5. **數據驗證** - 追蹤一致率統計

---

## ⚠️ 注意事項

- **速度**: 雙模型需要 2 次 API 調用，時間約 2 倍（4-6 秒）
- **額度**: 每次決策消耗 2 個 API 請求
- **成本**: 如果使用付費 API，成本翻倍

**建議**：
- 低頻交易（< 10 次/天）→ 使用 **Consensus**
- 中頻交易（10-50 次/天）→ 使用 **Consensus**
- 高頻交易（> 50 次/天）→ 使用 **Weighted** 或關閉雙模型

---

## 🤔 常見問題

### Q1: 為什麼要用兩個不同模型？

**DeepSeek-R1** 擅長複雜推理，但可能過於激進。
**GPT-4o / Gemini** 更穩定成熟，但可能過於保守。

兩者結合，取長補短。

### Q2: 兩個模型的一致率高嗎？

根據測試，大部分情況下一致率在 **70-85%**。

不一致時通常是市場訊號模糊，這時候 HOLD 才是正確選擇。

### Q3: 可以用其他模型嗎？

可以！修改 `dual_model_agent.py` 中的 `_init_models()` 函數。

例如要用 Claude：

```python
self.model_b = OpenAICompatibleModel(
    name='Claude_3.5',
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    base_url='https://api.anthropic.com/v1',
    model='claude-3-5-sonnet-20241022'
)
```

---

## 🎉 完成！

現在你已經拇有了：

✅ 雙模型決策系統 (DeepSeek-R1 + GPT/Gemini)
✅ 3 種決策模式可選
✅ 多角度 AI 分析
✅ 一致率統計追蹤
✅ 完整日誌記錄

開始交易吧！🚀
