# 多 API 輮换 + 多模型集成设置指南

## 🎯 核心优势

你每 15 分钟请求一次，每天只需 **96 次请求**，而免费 API 的额度远远超过这个数量：

| API | 每天额度 | 足够使用 |
|-----|---------|--------|
| **Groq** | 14,400 | ✅ 150 天 |
| **Google Gemini** | 1,500 | ✅ 15 天 |
| **OpenRouter** | 1,000 | ✅ 10 天 |
| **Cloudflare** | 10,000 | ✅ 104 天 |

通过多 API 轮换，你可以：
- ✅ **永久免费**使用所有顶级模型
- ✅ **多模型投票**提高决策准确性
- ✅ **自动故障转移**，无需关心额度
- ✅ **智能优先级**，根据场景选择最优模型

---

## 🚀 快速开始

### 1. 注册免费 API

#### A. Groq (最推荐 - 速度最快)
```bash
# 1. 访问 https://console.groq.com
# 2. 点击 "Sign Up" 注册
# 3. 选择 "API Keys" -> "Create API Key"
# 4. 复制 API Key（以 gsk_ 开头）
```

#### B. Google Gemini (推理最强)
```bash
# 1. 访问 https://aistudio.google.com
# 2. 登录 Google 账号
# 3. 点击 "Get API Key" -> "Create API Key"
# 4. 复制 API Key（以 AIzaSy 开头）
```

#### C. OpenRouter (多模型)
```bash
# 1. 访问 https://openrouter.ai
# 2. 点击 "Sign In" 登录
# 3. 选择 "Keys" -> "Create Key"
# 4. 复制 API Key（以 sk-or-v1- 开头）

# 提示：免费版每天 50 请求，但如果绑卡有 $10 credits，就是 1000/天
```

#### D. GitHub Models (可选)
```bash
# 1. 访问 https://github.com/marketplace/models
# 2. 使用你的 GitHub 账号登录
# 3. 创建 Personal Access Token
```

---

### 2. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env文件，填入你的 API Key
nano .env
```

**最小配置**（只需要 2 个）：
```bash
# .env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxx
```

**完整配置**（推荐）：
```bash
# .env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxx

# 多模型集成配置
ENABLE_ENSEMBLE=true
MIN_MODELS_FOR_CONSENSUS=2
MAX_MODELS_PER_REQUEST=3
```

---

### 3. 安装依赖

```bash
# 安装 Google AI SDK
pip install google-generativeai

# 更新其他依赖
pip install -U openai python-dotenv
```

---

### 4. 使用示例

```python
from core.llm_agent_ensemble import EnhancedTradingAgent

# 初始化 Agent
agent = EnhancedTradingAgent(enable_ensemble=True)

# 准备数据
market_data = {
    'close': 45000,
    'rsi': 35,
    'macd_hist': 0.0025,
    'adx': 28,
    'bb_position': 0.2,
    'atr': 250,
    'volume_ratio': 1.5
}

account_info = {
    'total_equity': 10000,
    'available_balance': 8000,
    'unrealized_pnl': 0
}

# 获取决策（多模型投票）
decision = agent.analyze_with_position(market_data, account_info)

print(f"\n决策: {decision['action']}")
print(f"信心度: {decision['confidence']}%")
print(f"杠杆: {decision['leverage']}x")
```

---

## 🤝 多模型集成决策原理

### 场景示例：

当你启用 `enable_ensemble=True` 后，每 15 分钟的更新会：

1. **同时请求 2-3 个不同模型**：
   - Google Gemini 2.5 Pro（推理最强）
   - Groq Llama 3.1 70B（速度最快）
   - OpenRouter DeepSeek R1（R1 推理链）

2. **各模型给出建议**：
   ```
   Gemini:  OPEN_LONG (信心 85%)
   Groq:    OPEN_LONG (信心 78%)
   OpenRouter: HOLD (信心 65%)
   ```

3. **投票机制**：
   - OPEN_LONG: 2 票
   - HOLD: 1 票
   - **最终决策**: OPEN_LONG (共识度 67%)
   - **平均信心度**: 81.5%

---

## 📊 智能 API 轮换策略

### 优先级系统

系统会根据**场景**自动选择最优 API：

| 场景 | 优先 API | 原因 |
|------|---------|------|
| **实时信号** | Groq | 极速响应 (200+ tokens/s) |
| **复杂分析** | Gemini 2.5 Pro | 推理能力最强 |
| **仓位管理** | Groq + Gemini | 快速 + 准确 |
| **集成决策** | 多 API 混合 | 避免单一模型偏见 |

### 故障转移

如果某个 API 不可用：
1. 自动尝试下一个可用 API
2. 连续失败 3 次，暂时禁用该 API
3. 每小时自动重置可用性

### 额度管理

系统自动追踪每个 API 的：
- 每分钟请求数 (RPM)
- 每天请求数
- 最后使用时间

---

## 🛠️ 高级配置

### 自定义场景优先级

编辑 `core/multi_api_manager.py`：

```python
def _setup_default_providers(self):
    # 调整优先级 (1-5, 5 最高)
    self.providers.append(APIProvider(
        name='Groq',
        priority=5  # 最高优先级
    ))
    
    self.providers.append(APIProvider(
        name='Google_Gemini',
        priority=5  # 最高优先级
    ))
```

### 禁用集成决策

如果你只想使用单个模型：

```python
# 在 .env 中
ENABLE_ENSEMBLE=false

# 或在代码中
agent = EnhancedTradingAgent(enable_ensemble=False)
```

### 调整模型数量

```bash
# .env
MIN_MODELS_FOR_CONSENSUS=2  # 最少 2 个模型
MAX_MODELS_PER_REQUEST=3    # 最多 3 个模型
```

---

## 📊 监控使用情况

```python
# 获取统计信息
stats = agent.get_stats()
print(json.dumps(stats, indent=2, ensure_ascii=False))
```

**输出示例**：
```json
{
  "total_providers": 3,
  "available_providers": 3,
  "providers": [
    {
      "name": "Groq",
      "model": "llama-3.1-70b-versatile",
      "daily_usage": "45/14400",
      "is_available": true,
      "priority": 5
    },
    {
      "name": "Google_Gemini",
      "model": "gemini-2.5-pro",
      "daily_usage": "32/1500",
      "is_available": true,
      "priority": 5
    },
    {
      "name": "OpenRouter_DSR1",
      "model": "deepseek-r1:free",
      "daily_usage": "18/1000",
      "is_available": true,
      "priority": 4
    }
  ]
}
```

---

## ❓ 常见问题

### Q1: 我只有一个 API Key，能用吗？
**A:** 可以！系统会自动使用你配置的 API。但建议至少配置 2 个（Groq + Gemini）以保证稳定性。

### Q2: 集成决策会消耗更多额度吗？
**A:** 会的。每次请求 2-3 个模型。但你的总额度远超过需求：
- 每天 96 次 x 3 模型 = 288 次
- Groq 额度: 14,400 次（足够 50 天）

### Q3: 如何仅使用 Groq 进行仓位管理？
**A:** 使用 `get_position_control()` 方法：
```python
decision = agent.get_position_control(market_data, account_info, position_info)
```

### Q4: 如何设置本地备用？
**A:** 如果所有 API 失败，系统会返回默认的 HOLD 决策。你可以修改 `_get_default_decision()` 调用本地 Ollama。

---

## 🚀 下一步

1. 注册至少 2 个 API Key
2. 配置 `.env` 文件
3. 运行 `python app_flask.py`
4. 启用自动更新，享受多模型集成决策！

**祝交易顺利！** 🚀📈
