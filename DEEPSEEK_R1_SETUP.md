# 🤖 DeepSeek R1 設置指南

## ✅ 已添加 DeepSeek R1 支持！

你的系統現在支持 **DeepSeek R1** - 與 OpenAI o1 效能相當的推理模型，但完全開源且成本低廉！

---

## 🎯 三種免費的 R1 API

### 1️⃣ OpenRouter (100% 免費) - **最推薦**

```json
{
  "OPENROUTER_API_KEY": "sk-or-v1-..."
}
```

**優勢**：
✅ 完全免費
✅ 每天 200 次請求
✅ 支持 2 個 R1 版本：
  - `deepseek/deepseek-r1-0528:free` (最新版)
  - `deepseek/deepseek-r1:free` (原始版)

**申請**：[openrouter.ai/keys](https://openrouter.ai/keys)

---

### 2️⃣ Scaleway (免費) - 備用

```json
{
  "SCALEWAY_API_KEY": "scw_..."
}
```

**優勢**：
✅ 免費 R1 Distill Llama 70B
✅ 每天 1000 次請求
✅ 歐洲伺服器，穩定

**申請**：[console.scaleway.com](https://console.scaleway.com)

---

### 3️⃣ DeepSeek 官方 API (付費但極便宜)

```json
{
  "DEEPSEEK_API_KEY": "sk-..."
}
```

**優勢**：
✅ 極低價格：$0.55/M input, $2.19/M output
✅ 只有 OpenAI o1 價格的 4%
✅ 無硬性限制，高額度
✅ 最快的 R1 響應速度

**申請**：[platform.deepseek.com](https://platform.deepseek.com)

---

## 🚀 快速開始

### 步驟 1: 更新代碼

```bash
cd STW
git pull origin main
```

### 步驟 2: 配置 API Key

修改 `config.json`：

```json
{
  "OPENROUTER_API_KEY": "sk-or-v1-...",
  "GROQ_API_KEY": "gsk_..."
}
```

### 步驟 3: 重啟系統

```bash
python app_flask.py
```

你應該看到：

```
✅ 已配置 9 個 API 提供商 (2026 可用模型 + DeepSeek R1)
  - OpenRouter_R1_0528_Free: deepseek/deepseek-r1-0528:free [R1] (優先級 5)
  - OpenRouter_R1_Free: deepseek/deepseek-r1:free [R1] (優先級 5)
  - OpenRouter_Gemini_2_Flash: google/gemini-2.0-flash-exp:free (優先級 4)
  - Groq_Llama_3_3_70B: llama-3.3-70b-versatile (優先級 5)
  ...
```

---

## 📊 效果展示

### 單模型使用 R1

```bash
AI 分析嘗試 1/3...
🤖 使用 API: OpenRouter_R1_0528_Free (deepseek/deepseek-r1-0528:free)
✅ AI 分析成功: OPEN_LONG (信心度 85%)
```

### 雙模型使用 R1

```bash
============================================================
🔍 雙模型決策系統啟動
Model A: OpenRouter_DeepSeek_R1_0528 (deepseek/deepseek-r1-0528:free)
Model B: Groq_Llama_3_3_70B (llama-3.3-70b-versatile)
============================================================

🤖 OpenRouter_DeepSeek_R1_0528 分析中...
✅ OpenRouter_DeepSeek_R1_0528: OPEN_LONG (信心度 88%)

🤖 Groq_Llama_3_3_70B 分析中...
✅ Groq_Llama_3_3_70B: OPEN_LONG (信心度 82%)

============================================================
⚡ 決策比對
============================================================
OpenRouter_DeepSeek_R1_0528: OPEN_LONG (88%)
  <思維鏈推理> RSI(28) 顯示超賣，MACD 出現金叉訊號，布林帶下軌反彈...

Groq_Llama_3_3_70B: OPEN_LONG (82%)
  市場超賣，成交量放大，技術指標支持多頭...

============================================================
✅ 最終決策
============================================================
Action: OPEN_LONG
Confidence: 85%
Reasoning: ✅ 兩個模型一致建議: OPEN_LONG
============================================================
```

---

## ⚙️ 雙模型配置

### 啟用雙模型 + R1

在 `config.json` 中添加：

```json
{
  "OPENROUTER_API_KEY": "sk-or-v1-...",
  "GROQ_API_KEY": "gsk_...",
  "use_dual_model": true,
  "dual_model_mode": "consensus"
}
```

**模型組合**：
- **Model A**: DeepSeek R1 (OpenRouter) - 推理能力極強
- **Model B**: Llama 3.3 70B (Groq) - 速度快且穩定

---

## 📈 R1 vs 其他模型

| 特性 | DeepSeek R1 | Llama 3.3 70B | Gemini 2.0 | GPT-4o-mini |
|------|-------------|---------------|------------|-------------|
| 推理能力 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 速度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 思維鏈 | ✅ 透明 | ❌ | ❌ | ❌ |
| 免費額度 | 200/天 | 14400/天 | 1500/天 | 1000/天 |
| 成本 | $0 / $0.55 | $0 | $0 | $0 |
| Context | 163K | 128K | 1M | 128K |

---

## 🔥 R1 的獨特優勢

### 1. 透明思維鏈

R1 會展示完整的推理過程，你可以看到：
- 如何分析技術指標
- 如何比對不同訊號
- 如何得出最終結論

### 2. 與 o1 相當的效能

- OpenAI o1: **$15/M input, $60/M output**
- DeepSeek R1: **$0.55/M input, $2.19/M output** (4% 的價格！)

### 3. 開源且可商用

- MIT 授權
- 可以用於訓練和 distillation
- 671B 參數，37B 活躍

---

## ⚠️ 注意事項

### OpenRouter 免費版限制

- 每天 **200 次請求**
- 每分鐘 **20 次請求**
- 可能需要排隊（尖峰時段）

### R1 響應時間

- 比一般模型慢 **2-3 倍** (因為思維鏈)
- 單次請求約 **4-8 秒**
- 雙模型會更慢 (**10-15 秒**)

### 建議

- **低頻交易** (< 20 次/天) → 使用 R1 雙模型
- **中頻交易** (20-100 次/天) → 使用 R1 單模型
- **高頻交易** (> 100 次/天) → 使用 Llama 3.3 70B

---

## 🤔 常見問題

### Q1: R1 比其他模型好嗎？

在**複雜推理**和**多步驟分析**中，R1 明顯優於 Llama/Gemini。

但在**簡單任務**和**速度要求高**時，Llama 3.3 更合適。

### Q2: 為什麼 R1 這麼慢？

R1 使用 **思維鏈** (Chain-of-Thought)，會先在內部思考 20-50 秒，然後再輸出結果。

這是換取更高準確性的代價。

### Q3: 可以同時用多個 R1 API 嗎？

可以！系統會自動輪換：

```json
{
  "OPENROUTER_API_KEY": "sk-or-...",
  "SCALEWAY_API_KEY": "scw_...",
  "DEEPSEEK_API_KEY": "sk-..."
}
```

額度合計：200 + 1000 + 無限 = 大量額度

---

## 🎉 完成！

現在你已經擁有：

✅ DeepSeek R1 免費 API 支持
✅ 雙模型決策（R1 + Llama 3.3）
✅ 多 API 自動輪換
✅ 透明思維鏈推理
✅ 與 OpenAI o1 相當的效能

開始交易吧！🚀

---

## 🔗 相關連結

- [DeepSeek R1 技術報告](https://github.com/deepseek-ai/DeepSeek-R1)
- [OpenRouter R1 文檔](https://openrouter.ai/deepseek/deepseek-r1)
- [DeepSeek 官方 API](https://platform.deepseek.com)
- [Scaleway API](https://console.scaleway.com)
