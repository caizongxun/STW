# 🤝 雙模型決策系統使用指南

## 概述

雙模型決策系統使用**兩個獨立的 AI 模型**同時分析市場，然後比對結果，提高決策的準確性和可靠性。

## 系統架構

```
市場數據
    ↓
├── Model A (DeepSeek-R1) ───┐
│                              │
├── Model B (備用模型) ───┤ → 決策比對
│                              │
└─────────────────────┘
         ↓
    最終決策
```

## 三種決策模式

### 1. **Consensus 模式（共識）**
- **逻輯**: 兩個模型必須完全一致
- **一致時**: 取平均信心度，執行決策
- **不一致時**: 強制 HOLD，等待更明確訊號
- **優點**: 最安全，避免錯誤決策
- **缺點**: 可能錯過機會

**範例**:
```
Model A: OPEN_LONG (80%)
Model B: OPEN_LONG (75%)
→ 結果: OPEN_LONG (77.5%)

---

Model A: OPEN_LONG (80%)
Model B: HOLD (60%)
→ 結果: HOLD (30%) ⚠️ 意見不一致
```

---

### 2. **Vote 模式（投票）**
- **逻輯**: 簡單多數決
- **行為**: 目前與 Consensus 相同
- **適用**: 2 個模型時與 Consensus 相同，3+ 模型時可拓展

---

### 3. **Weighted 模式（加權）**
- **逻輯**: 信心度高的模型權重更大
- **一致時**: 取平均
- **不一致時**: 選擇信心度高的，但降低至 70%
- **優點**: 更靈活，不會錯過所有機會
- **缺點**: 有風險，需要謹慎使用

**範例**:
```
Model A: OPEN_LONG (85%)
Model B: HOLD (60%)
→ 結果: OPEN_LONG (59.5%) ⚠️ 降低信心度和倉位
```

---

## 使用方法

### 方法1: Python 直接調用

```python
from core.dual_model_agent import DualModelDecisionAgent
from strategies.v13.market_features import prepare_market_features

# 初始化雙模型系統
dual_agent = DualModelDecisionAgent()

# 準備數據
market_data = prepare_market_features(df.iloc[-1], df)
account_info = {
    'total_equity': 10000,
    'available_balance': 10000,
    'unrealized_pnl': 0,
    'max_leverage': 10
}

# 共識模式（預設）
decision = dual_agent.analyze_with_dual_models(
    market_data=market_data,
    account_info=account_info,
    position_info=None,
    mode='consensus'  # 或 'vote', 'weighted'
)

print(f"決策: {decision['action']}")
print(f"信心度: {decision['confidence']}%")
print(f"理由: {decision['reasoning']}")
```

---

### 方法2: Flask API 修改

修改 `app_flask.py` 中的 `analyze_market()` 函數：

```python
# 原本 (單模型)
if not app_state['ai_agent']:
    app_state['ai_agent'] = PositionAwareDeepSeekAgent()

decision = app_state['ai_agent'].analyze_with_position(
    market_data=latest_data,
    account_info=account_info,
    position_info=position_info
)

# ---

# 更改為 (雙模型)
from core.dual_model_agent import DualModelDecisionAgent

if not app_state.get('dual_agent'):
    app_state['dual_agent'] = DualModelDecisionAgent()

decision = app_state['dual_agent'].analyze_with_dual_models(
    market_data=latest_data,
    account_info=account_info,
    position_info=position_info,
    mode='consensus'  # 可配置
)
```

---

## 輸出示例

```bash
============================================================
🔍 雙模型決策系統啟動
============================================================

🤖 Model A (DeepSeek-R1) 分析中...
AI 分析嘗試 1/3...
🤖 使用 API: Groq_R1_Distill (deepseek-r1-distill-llama-70b)
✅ Groq_R1_Distill 請求成功
✅ AI 分析成功: OPEN_LONG (信心度 82%)

🤖 Model B (備用模型) 分析中...
AI 分析嘗試 1/3...
🤖 使用 API: OpenRouter_R1 (deepseek/deepseek-r1:free)
✅ OpenRouter_R1 請求成功
✅ AI 分析成功: OPEN_LONG (信心度 78%)

============================================================
⚡ 決策比對
============================================================
Model A: OPEN_LONG (信心度 82%)
  理由: RSI 超賣 + MACD 金叉...

Model B: OPEN_LONG (信心度 78%)
  理由: 布林帶下軌反彈...

============================================================
✅ 最終決策
============================================================
Action: OPEN_LONG
Confidence: 80%
Reasoning: ✅ 兩個模型一致建議: OPEN_LONG. A: RSI 超賣... | B: 布林帶...
============================================================
```

---

## 性能統計

```python
# 獲取一致率
agreement_rate = dual_agent.get_agreement_rate(last_n=10)
print(f"最近 10 次決策一致率: {agreement_rate:.1f}%")

# 獲取詳細統計
stats = dual_agent.get_model_performance()
print(f"總決策次數: {stats['total_decisions']}")
print(f"一致次數: {stats['agreements']}")
print(f"分歧次數: {stats['disagreements']}")
print(f"一致率: {stats['agreement_rate']:.1f}%")
```

---

## 優勢

✅ **更高準確性**: 兩個模型互相驗證
✅ **降低風險**: 意見不一致時保守策略
✅ **提高信心**: 共識決策更可靠
✅ **多角度分析**: 不同模型的推理角度
✅ **數據驗證**: 追蹤一致率統計

---

## 注意事項

⚠️ **速度**: 需要調用兩次 API，時間約 2倍
⚠️ **額度**: 消耗兩個 API 請求
⚠️ **成本**: 如果使用付費 API，成本翻倍

---

## 建議配置

### 低頻交易 (每天 < 10 次)
- 模式: **Consensus**
- 原因: 最安全，確保每次都是高質量決策

### 中頻交易 (每天 10-50 次)
- 模式: **Vote** 或 **Consensus**
- 原因: 平衡安全和機會

### 高頻交易 (每天 > 50 次)
- 模式: **Weighted**
- 原因: 不會錯過太多機會，但需要謹慎

---

## 快速開始

```bash
# 1. 更新代碼
git pull origin main

# 2. 測試雙模型
python -c "
from core.dual_model_agent import DualModelDecisionAgent
print('✅ 雙模型系統已就緒')
"

# 3. 啟動 Flask
python app_flask.py
```

現在你已經有了雙模型決策系統！
