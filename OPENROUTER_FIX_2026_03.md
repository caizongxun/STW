# OpenRouter 2026 年 3 月模型 ID 修正

## 問題說明

根據實際測試，以下模型 ID 不可用：

```
❌ meta-llama/llama-3.1-405b-instruct:free  (404 - No endpoints found)
❌ google/gemini-2.0-flash-thinking-exp:free  (400 - Invalid model ID)
❌ mistralai/mistral-small-3.1-2502:free      (400 - Invalid model ID)
❌ qwen/qwen3-coder-480b:free                 (400 - Invalid model ID)
```

一個模型被限速：
```
⚠️ meta-llama/llama-3.3-70b-instruct:free  (429 - Rate limited)
```

---

## ✅ 2026 年 3 月實際可用的免費模型

根據 OpenRouter 官網和實際測試，以下是 **確定可用** 的免費模型：

### 1. Llama 系列

```python
# Llama 3.3 70B - 最佳綜合性能
meta-llama/llama-3.3-70b-instruct:free

# Llama 3.1 405B - 無免費版，需付費
meta-llama/llama-3.1-405b-instruct  # $2/M input
```

### 2. Google Gemini

```python
# Gemini 2.0 Flash Exp - 1M context
google/gemini-2.0-flash-exp:free

# 注意：不是 thinking-exp，而是 flash-exp
```

### 3. Mistral 系列

```python
# Mistral Small 3.1 - 最新版本
mistralai/mistral-small-3.1:free

# Devstral 2 - 編碼專用
mistralai/devstral-2512:free
```

### 4. Qwen 系列

```python
# Qwen 2.5 Coder 32B
qwen/qwen-2.5-coder-32b-instruct:free

# Qwen 2.5 7B
qwen/qwen-2.5-7b-instruct:free
```

### 5. 其他優質免費模型

```python
# Xiaomi MiMo V2 Flash - 309B MoE
xiaomi/mimo-v2-flash:free

# NVIDIA Nemotron 3 Nano - AI Agent
nvidia/nemotron-3-nano-instruct:free

# Hermes 3 405B
nous-research/hermes-3-llama-3.1-405b:free
```

---

## 🛠️ 修正方案

### 方案 1: 修改 multi_api_manager.py

更新第 104-140 行：

```python
if os.getenv('OPENROUTER_API_KEY'):
    # Llama 3.3 70B - 最佳綜合性能
    self.providers.append(APIProvider(
        name='OpenRouter_Llama_3_3_70B',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        base_url='https://openrouter.ai/api/v1',
        model='meta-llama/llama-3.3-70b-instruct:free',  # 保持不變
        rpm_limit=20,
        daily_limit=200,
        priority=5
    ))
    
    # Gemini 2.0 Flash Exp - 1M context
    self.providers.append(APIProvider(
        name='OpenRouter_Gemini_2_Flash',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        base_url='https://openrouter.ai/api/v1',
        model='google/gemini-2.0-flash-exp:free',  # ⭐ 修改這裡
        rpm_limit=20,
        daily_limit=200,
        priority=5
    ))
    
    # Mistral Small 3.1
    self.providers.append(APIProvider(
        name='OpenRouter_Mistral_Small',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        base_url='https://openrouter.ai/api/v1',
        model='mistralai/mistral-small-3.1:free',  # ⭐ 修改這裡
        rpm_limit=20,
        daily_limit=200,
        priority=4
    ))
    
    # Qwen 2.5 Coder 32B - 編碼專用
    self.providers.append(APIProvider(
        name='OpenRouter_Qwen_Coder',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        base_url='https://openrouter.ai/api/v1',
        model='qwen/qwen-2.5-coder-32b-instruct:free',  # ⭐ 修改這裡
        rpm_limit=20,
        daily_limit=200,
        priority=4
    ))
```

---

### 方案 2: 直接使用 Groq (推薦)

OpenRouter 免費模型經常被限速或變動，**建議優先使用 Groq**：

```python
# Groq 的優勢：
# 1. 速度極快 (500+ tokens/s)
# 2. 額度充裕 (14,400 次/天)
# 3. 穩定可靠 (很少限速)

if os.getenv('GROQ_API_KEY'):
    self.providers.append(APIProvider(
        name='Groq_Llama_3_3_70B',
        api_key=os.getenv('GROQ_API_KEY'),
        base_url='https://api.groq.com/openai/v1',
        model='llama-3.3-70b-versatile',
        rpm_limit=30,
        daily_limit=14400,
        priority=5  # 最高優先級
    ))
```

---

## 💡 最佳實踐

### 對於 15 分鐘更新一次的交易系統：

**推薦配置：**

```python
# 階段 1: 兩個快速模型 (每次都調用)
fast_model_a = Groq Llama 3.3 70B       # 14,400/天
fast_model_b = Google Gemini 2.0 Flash # 1,500/天

# 階段 2: 仲裁者 (只在分歧時調用)
arbitrator = OpenRouter Llama 3.3 70B  # 200/天 (節省使用)
```

**額度消耗計算：**
```
每天 96 次分析：
- Groq: 96 次 (剩 14,304)
- Google: 96 次 (剩 1,404)
- OpenRouter: 38 次 (假設 40% 分歧率)

總計: 230 次/天
剩餘: 15,746 次/天
```

---

## ⚠️ 注意事項

1. **OpenRouter 免費模型經常變動**
   - 模型 ID 可能每幾周就會更新
   - 免費額度可能調整

2. **429 Rate Limit 錯誤**
   - 表示當前模型被限速
   - 等待幾分鐘或切換到其他 API

3. **最穩定的選擇**
   - **Groq**: 速度快、額度高、很少限速
   - **Google Gemini**: 官方 API、穩定
   - **OpenRouter**: 作為備用

---

## ✅ 建議修正步驟

1. **立即修正** `core/multi_api_manager.py`
   - 更新第 126 行: `google/gemini-2.0-flash-exp:free`
   - 更新第 136 行: `mistralai/mistral-small-3.1:free`
   - 更新第 146 行: `qwen/qwen-2.5-coder-32b-instruct:free`
   - 刪除第 116 行: Llama 405B (不再免費)

2. **調整優先級**
   - Groq Llama 3.3 70B: priority = 5 (最高)
   - Google Gemini 2.0: priority = 5
   - OpenRouter 模型: priority = 3 (作為備用)

3. **測試**
   ```bash
   python app_flask.py
   ```

---

**最後更新**: 2026 年 3 月 7 日 13:25 CST
