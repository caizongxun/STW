# OpenRouter 免費模型設定指南

## 為什麼需要 OpenRouter？

### Gemini 的問題
❌ **Gemini 免費版有嚴格限制：**
- 15 requests/分鐘
- 1,500 requests/天
- 超過就 429 Error

✅ **OpenRouter 全部免費，更多選擇：**
- 20 requests/分鐘
- 200 requests/天
- 多個高品質模型
- **包含 DeepSeek！**

---

## 步驟 1: 申請 OpenRouter API Key

### 1.1 註冊帳號

1. 前往 [https://openrouter.ai](https://openrouter.ai)
2. 點擊 **Sign Up** 或 **Get Started**
3. 使用 Google/GitHub 帳號登入（或使用 Email）

### 1.2 獲取 API Key

1. 登入後，點擊右上角**頭像**
2. 選擇 **API Keys**
3. 點擊 **Create New Key**
4. 輸入名稱（例如：`STW Trading Bot`）
5. 點擊 **Create**
6. **複製 API Key**（以 `sk-or-v1-` 開頭）

⚠️ **重要：**API Key 只顯示一次，請妄善保管！

---

## 步驟 2: 配置 API Key

### 方法 A: 使用 Web UI（推薦）

1. 打開 http://localhost:5000
2. 點擊 **配置** (Config) 標籤
3. 在 **OpenRouter API Key** 輸入框貼上 API Key
4. 點擊 **保存配置**
5. 點擊 **測試 API 連接**

看到 ✅ 表示成功！

### 方法 B: 手動編輯 config.json

```json
{
  "api_keys": {
    "openrouter": "sk-or-v1-YOUR_KEY_HERE"
  }
}
```

### 方法 C: 設定環境變數

**Windows:**
```cmd
set OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
python app_flask.py
```

**Linux/Mac:**
```bash
export OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE"
python app_flask.py
```

---

## 步驟 3: 驗證設定

### 3.1 檢查啟動輸出

重啟 Flask 後，你會看到：

```
🏆 兩階段仲裁決策系統啟動 (全部免費模型)
======================================================================
✅ 快速模型 A: Llama 3.3 70B (Groq) - 速度極快
✅ 快速模型 B: DeepSeek V3 (OpenRouter) - 通用強
✅ 仲裁者: Llama 3.1 405B (OpenRouter) - 免費最強

💡 策略: 兩個快速模型分析 → 同意則執行，分歧則由 405B 仲裁
🆓 全部免費: OpenRouter (20 req/min, 200 req/day)
======================================================================
```

### 3.2 測試分析

1. 打開 http://localhost:5000
2. 點擊 **分析**
3. 看到：

```
🤖 [DeepSeek_V3] 分析中...
✅ [DeepSeek_V3]: OPEN_LONG (信心度 75%) - 3.2s
```

---

## 現在你有的模型配置

### 優先順序（自動備援）

| 角色 | 第一選擇 | 備用 | 速度 | 品質 |
|------|---------|------|------|------|
| **快速 A** | Llama 70B (Groq) | DeepSeek R1 (OpenRouter) | ⭐️⭐️⭐️⭐️⭐️ | ⭐️⭐️⭐️⭐️ |
| **快速 B** | DeepSeek V3 (OpenRouter) | Gemini 2.0 (Google) | ⭐️⭐️⭐️⭐️ | ⭐️⭐️⭐️⭐️⭐️ |
| **仲裁者** | Llama 405B (OpenRouter) | - | ⭐️⭐️⭐️ | ⭐️⭐️⭐️⭐️⭐️ |

### 備用邏輯

1. **Groq 有 API Key** → 使用 Llama 70B（速度最快）
2. **Groq 沒有** → 使用 OpenRouter DeepSeek R1
3. **OpenRouter 有 API Key** → 使用 DeepSeek V3
4. **OpenRouter 沒有** → 使用 Gemini
5. **兩個模型分歧** → 調用 Llama 405B 仲裁

---

## OpenRouter 免費模型列表

### 適合交易的模型（推理能力強）

| 模型 | ID | 特點 |
|------|-----|------|
| **DeepSeek R1** | `deepseek/deepseek-r1:free` | 推理最強，適合複雜分析 |
| **DeepSeek V3** | `deepseek/deepseek-chat:free` | 通用型，速度快 |
| **Llama 3.3 70B** | `meta-llama/llama-3.3-70b-instruct:free` | Meta 最新，平衡|
| **Llama 3.1 405B** | `meta-llama/llama-3.1-405b-instruct:free` | 最強免費模型 |
| **Mistral Small** | `mistralai/mistral-small-3.1:free` | 歐洲模型，穩定 |
| **Qwen Coder** | `qwen/qwen-2.5-coder-32b-instruct:free` | 阿里巴巴，代碼能力強 |

### 其他免費模型（共 24 個）

查看完整列表：[https://openrouter.ai/models/?q=free](https://openrouter.ai/models/?q=free)

---

## 常見問題

### Q1: OpenRouter 真的完全免費嗎？

A: **是的！**
- 不需要信用卡
- 標有 `:free` 的模型完全免費
- 限制：20 req/min, 200 req/day

### Q2: DeepSeek 和 Gemini 比較？

| 項目 | DeepSeek | Gemini |
|------|----------|--------|
| **推理能力** | ⭐️⭐️⭐️⭐️⭐️ | ⭐️⭐️⭐️⭐️ |
| **速度** | ⭐️⭐️⭐️⭐️ | ⭐️⭐️⭐️⭐️⭐️ |
| **穩定性** | ⭐️⭐️⭐️⭐️⭐️ | ⭐️⭐️⭐️ (429 Error) |
| **限制** | 20/min, 200/day | 15/min, 1500/day |
| **交易分析** | ✅ 很強 | ✅ 不錯 |

**結論：DeepSeek 更適合高頻率交易分析**

### Q3: 可以同時配置多個 API Key 嗎？

A: **可以！**

```json
{
  "api_keys": {
    "groq": "gsk_...",
    "openrouter": "sk-or-v1-...",
    "google": "AIza..."
  }
}
```

系統會自動選擇最佳組合！

### Q4: 如果所有模型都失敗怎麼辦？

A: 系統會自動 **HOLD**，不會交易。

---

## 下一步

現在你有：
- ✅ 40 個技術指標
- ✅ 歷史 20 根 K 棒
- ✅ 成功案例學習
- ✅ 多個免費模型備用
- ✅ DeepSeek 推理能力

建議：
1. **配置 OpenRouter API Key**
2. **重啟 Flask**
3. **測試分析功能**
4. **觀察 1-2 天，比較準確率**

需要幫忙配置嗎？
