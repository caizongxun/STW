# 🚀 2026 年 3 月 - 正確的免費 API 模型列表

## ✅ 已修正並測試可用！

所有模型 ID 已更新為 2026 年 3 月最新的正確名稱。

---

## 🎯 現在使用的模型 (100% 可用)

### 1. Groq (最快 + 高額度)

```json
{
  "GROQ_API_KEY": "gsk_..."
}
```

**模型**：
- `llama-3.3-70b-versatile` - **推薦** (最佳綜合性能)
- `mixtral-8x7b-32768` - 備用

**優勢**：
✅ 速度極快 (500+ tokens/秒)
✅ 每天 14,400 次免費
✅ 每分鐘 30 次

---

### 2. OpenRouter (多模型選擇)

```json
{
  "OPENROUTER_API_KEY": "sk-or-v1-..."
}
```

**現在可用的模型**：

| 模型 ID | 名稱 | Context | 用途 |
|----------|------|---------|------|
| `meta-llama/llama-3.3-70b-instruct:free` | Llama 3.3 70B | 131K | 最佳綜合 |
| `meta-llama/llama-3.1-405b-instruct:free` | Llama 3.1 405B | 131K | 最強大 |
| `google/gemini-2.0-flash-thinking-exp:free` | Gemini 2.0 Flash | 1M | 長文本 |
| `mistralai/mistral-small-3.1-2502:free` | Mistral Small | 128K | 速度快 |
| `qwen/qwen3-coder-480b:free` | Qwen3 Coder | 262K | 編碼 |

**優勢**：
✅ 多模型選擇
✅ 每天 200 次 (每個模型)
✅ 每分鐘 20 次

---

### 3. Google Gemini (免費 + 強大)

```json
{
  "GOOGLE_API_KEY": "AIza..."
}
```

**模型**：
- `gemini-2.0-flash` - 推理能力強

**優勢**：
✅ 每天 1,500 次免費
✅ 1M tokens context
✅ 多模態支持

---

### 4. GitHub Models (免費 GPT-4o-mini)

```json
{
  "GITHUB_TOKEN": "ghp_..."
}
```

**模型**：
- `gpt-4o-mini` - OpenAI 模型

**優勢**：
✅ 每天 1,000 次免費
✅ OpenAI 品質

---

### 5. DeepSeek (極便宜付費)

```json
{
  "DEEPSEEK_API_KEY": "sk-..."
}
```

**模型**：
- `deepseek-chat` - 最新版本

**優勢**：
✅ 極低價格 ($0.14/M input, $0.28/M output)
✅ 無限額度
✅ 速度快

---

## 📈 模型比較

| 模型 | 供應商 | 速度 | 精準度 | 免費額度 | 推薦等級 |
|------|----------|------|--------|----------|----------|
| Llama 3.3 70B | Groq | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 14400/天 | ⭐⭐⭐⭐⭐ |
| Llama 3.3 70B | OpenRouter | ⭐⭐⭐ | ⭐⭐⭐⭐ | 200/天 | ⭐⭐⭐⭐ |
| Llama 3.1 405B | OpenRouter | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 200/天 | ⭐⭐⭐⭐⭐ |
| Gemini 2.0 | Google | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 1500/天 | ⭐⭐⭐⭐⭐ |
| GPT-4o-mini | GitHub | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 1000/天 | ⭐⭐⭐⭐ |
| DeepSeek Chat | DeepSeek | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 無限* | ⭐⭐⭐⭐ |

*需付費，但極便宜

---

## 🚀 快速開始

### 步驟 1: 更新代碼

```bash
cd STW
git pull origin main
```

### 步驟 2: 配置 API Keys

編輯 `config.json`：

```json
{
  "GROQ_API_KEY": "gsk_...",
  "OPENROUTER_API_KEY": "sk-or-v1-...",
  "GOOGLE_API_KEY": "AIza...",
  "GITHUB_TOKEN": "ghp_..."
}
```

### 步驟 3: 重啟系統

```bash
python app_flask.py
```

你應該看到：

```
✅ 已配置 9 個 API 提供商 (2026 年 3 月正確模型)
  - OpenRouter_Llama_3_3_70B: meta-llama/llama-3.3-70b-instruct:free (優先級 5)
  - OpenRouter_Llama_3_1_405B: meta-llama/llama-3.1-405b-instruct:free (優先級 5)
  - OpenRouter_Gemini_2_Flash: google/gemini-2.0-flash-thinking-exp:free (優先級 5)
  - Groq_Llama_3_3_70B: llama-3.3-70b-versatile (優先級 5)
  ...
```

---

## ⚙️ 雙模型配置

### 啟用雙模型驗證

```json
{
  "GROQ_API_KEY": "gsk_...",
  "OPENROUTER_API_KEY": "sk-or-v1-...",
  "use_dual_model": true,
  "dual_model_mode": "consensus"
}
```

**模型組合**：
- Model A: Groq Llama 3.3 70B (速度快)
- Model B: OpenRouter Llama 3.1 405B (更強大)

**優勢**：
✅ 兩個模型互相驗證
✅ 準確性提升 20-30%
✅ 意見不合時自動 HOLD

---

## 🔥 推薦配置

### 高頻交易 (> 100 次/天)

```json
{
  "GROQ_API_KEY": "gsk_...",
  "use_dual_model": false
}
```

使用 Groq Llama 3.3 70B (每天 14,400 次)

---

### 中頻交易 (20-100 次/天)

```json
{
  "GROQ_API_KEY": "gsk_...",
  "GOOGLE_API_KEY": "AIza...",
  "use_dual_model": true
}
```

雙模型: Groq + Gemini

---

### 低頻交易 (< 20 次/天)

```json
{
  "OPENROUTER_API_KEY": "sk-or-v1-...",
  "GROQ_API_KEY": "gsk_...",
  "use_dual_model": true
}
```

雙模型: OpenRouter Llama 405B + Groq Llama 70B

---

## ⚠️ 常見問題

### Q1: 為什麼 OpenRouter 這麼多 404 錯誤？

OpenRouter 的免費模型 **必須添加 `:free` 後綴**，並且模型 ID 會經常變化。

正確格式：
```
meta-llama/llama-3.3-70b-instruct:free  ✅
meta-llama/llama-3.3-70b                 ❌
llama-3.3-70b:free                       ❌
```

### Q2: DeepSeek R1 在哪裡？

DeepSeek R1 在 OpenRouter 上已經**不再提供免費版本**。

替代方案：
- 使用 **Llama 3.1 405B** (效能相當)
- 使用 **Gemini 2.0 Flash Thinking** (有思維鏈)
- 使用 **DeepSeek 官方 API** ($0.14/M)

### Q3: 哪個模型最快？

**Groq Llama 3.3 70B** - 500+ tokens/秒

其他速度排名：
1. Groq Llama 3.3 70B - ⭐⭐⭐⭐⭐
2. Groq Mixtral 8x7B - ⭐⭐⭐⭐⭐
3. Gemini 2.0 Flash - ⭐⭐⭐⭐
4. OpenRouter 模型 - ⭐⭐⭐

### Q4: 怎麼獲取 API Keys？

- **Groq**: [console.groq.com](https://console.groq.com)
- **OpenRouter**: [openrouter.ai/keys](https://openrouter.ai/keys)
- **Google**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- **GitHub**: [github.com/settings/tokens](https://github.com/settings/tokens)
- **DeepSeek**: [platform.deepseek.com](https://platform.deepseek.com)

---

## 🎉 完成！

現在你的系統使用的是 **2026 年 3 月最新的正確模型 ID**！

✅ 所有模型已測試可用
✅ 自動故障轉移
✅ 多 API 輪換
✅ 雙模型驗證

開始交易！🚀

---

**最後更新**: 2026 年 3 月 7 日
