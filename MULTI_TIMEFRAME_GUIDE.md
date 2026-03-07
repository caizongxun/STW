# 多時間框架分析 + 逆勢操作指南

## ✅ 已完成功能

### 1. 多時間框架分析 ([commit c83b26b](https://github.com/caizongxun/STW/commit/c83b26bd4096702dab3a4fa006603be20613d282))

✅ **支持 3 個時間框架**
- **15m** (主時間框架): 進出場時機
- **1h** (輔助): 判斷中期趨勢
- **4h** (輔助): 判斷大趨勢

✅ **每個時間框架包含**
- 當前 K 棒的全部 40 種指標
- 前 20 根歷史 K 棒 (每根也是 40 種指標)
- 趨勢分析: UP/DOWN/SIDEWAYS
- 強度: 0-100

---

### 2. 逆勢操作機制

✅ **允許 AI 在高信心度時逆勢操作**

#### 逆勢操作條件：

1. **15m 超賣/超買**
   - RSI < 30 (超賣)
   - RSI > 70 (超買)

2. **1h 趨勢明確**
   - 趨勢強度 > 50
   - EMA 排列有序

3. **信心度高**
   - 至少 75%

4. **緊停損**
   - 1-2% 範圍內

#### 逆勢操作範例：

**情境 1: 逆勢做多**
```
15m: RSI = 25 (超賣)
1h: 強勁上升趨勢 (強度 = 65)
4h: 上升趨勢

→ AI 可以在 15m 高信心度 (75-80%) 做多
→ 停損: 1-2%
→ 持倉時間: 1小時內
```

**情境 2: 逆勢做空**
```
15m: RSI = 75 (超買)
1h: 強勁下跌趨勢 (強度 = 70)
4h: 下跌趨勢

→ AI 可以在 15m 高信心度 (75-80%) 做空
→ 停損: 1-2%
→ 持倉時間: 1小時內
```

---

## 📊 多時間框架數據結構

### AI 收到的完整資訊：

```json
{
  "15m": {
    "timeframe": "15m",
    "current": {
      "close": 50000,
      "rsi": 45.2,
      "ema9": 50150,
      "macd": 12.5,
      ... // 40 種指標
    },
    "candles": [
      {
        "timestamp": "2026-03-07 18:00:00",
        "open": 50000,
        "high": 50500,
        "low": 49800,
        "close": 50200,
        "volume": 1234.5,
        "features": {...} // 40 種指標
      },
      ... // 共 20 根
    ],
    "trend": "UP",
    "strength": 65.2,
    "summary": "強勁上升趨勢 (ADX=43.5, RSI=45.2)"
  },
  "1h": {
    "timeframe": "1h",
    "current": {...},
    "candles": [...],
    "trend": "UP",
    "strength": 72.1,
    "summary": "強勁上升趨勢 (ADX=48.1, RSI=58.3)"
  },
  "4h": {
    "timeframe": "4h",
    "current": {...},
    "candles": [...],
    "trend": "UP",
    "strength": 68.5,
    "summary": "温和上升趨勢 (ADX=45.7, RSI=62.1)"
  }
}
```

---

## 🤖 AI Prompt 更新

### System Prompt 加入：

```
4. **結合多時間框架** (15m + 1h + 4h) 看清大趨勢

- **主時間框架為 15分鐘**，但要參考 1h 和 4h 趨勢
- **允許逆勢操作**：在信心度高 (>75%) 且技術指標強勁時，
  可以在 **1小時內** 做 15分鐘的逆勢操作
  
- **逆勢條件**：
  * 15m 超賣/超買 (RSI<30 or RSI>70)
  * 1h 趨勢明確 (但 15m 短線反轉訊號)
  * 信心度 > 75%
  * 停損要緊 (1-2%)
```

### User Prompt 加入：

```
=== 多時間框架分析 ===

** 注意 **：使用 1h 和 4h 判斷大趨勢，15m 做進出場時機
** 逆勢策略 **：如果 15m 超賣且 1h 看漲，可以高信心做多 (或相反)

{
  "15m": {...},
  "1h": {...},
  "4h": {...}
}
```

### 輸出 JSON 新增欄位：

```json
{
  "action": "OPEN_LONG",
  "confidence": 78,
  "is_counter_trend": true,  // 新增！
  ...
}
```

---

## 🔧 使用方法

### 1. 在 `app_flask.py` 中使用

```python
from core.multi_timeframe_analyzer import MultiTimeframeAnalyzer

# 初始化
mt_analyzer = MultiTimeframeAnalyzer(data_loader)

# 獲取多時間框架數據
multi_tf_data = mt_analyzer.prepare_multi_timeframe_data(
    symbol='BTCUSDT',
    primary_timeframe='15m',
    secondary_timeframes=['1h', '4h'],
    num_candles=20
)

# 檢查逆勢機會
counter_signal = mt_analyzer.get_counter_trend_signal(multi_tf_data)
if counter_signal['has_signal']:
    print(f"🚨 高信心逆勢機會: {counter_signal['direction']}")
    print(f"   信心度: {counter_signal['confidence']}%")
    print(f"   理由: {counter_signal['reasoning']}")

# 傳遞給 AI
decision = arbitrator_agent.analyze_with_arbitration(
    market_data=current_market_data,
    account_info=account_info,
    position_info=position_info,
    historical_candles=historical_candles_15m,
    successful_cases=successful_cases,
    multi_timeframe_data=multi_tf_data  # 新增！
)
```

### 2. 修改 `analyze_market` API

需要在 `@app.route('/api/analyze', methods=['POST'])` 中加入：

```python
# 初始化多時間框架分析器
if not hasattr(app_state['data_loader'], 'mt_analyzer'):
    from core.multi_timeframe_analyzer import MultiTimeframeAnalyzer
    app_state['data_loader'].mt_analyzer = MultiTimeframeAnalyzer(
        app_state['data_loader']
    )

# 獲取多時間框架數據
mt_analyzer = app_state['data_loader'].mt_analyzer
multi_tf_data = mt_analyzer.prepare_multi_timeframe_data(
    symbol=symbol,
    primary_timeframe=timeframe,
    secondary_timeframes=['1h', '4h'],
    num_candles=20
)

# 傳遞給 AI 決策函數
decision = _get_ai_decision(
    market_data=latest_data,
    account_info=account_info,
    position_info=position_info,
    historical_candles=historical_candles,
    successful_cases=app_state['cases'][:10],
    multi_timeframe_data=multi_tf_data  # 新增！
)
```

### 3. 修改 `_get_ai_decision` 函數

```python
def _get_ai_decision(
    market_data: Dict,
    account_info: Dict,
    position_info: Optional[Dict],
    historical_candles: Optional[List[Dict]] = None,
    successful_cases: Optional[List[Dict]] = None,
    multi_timeframe_data: Optional[Dict] = None  # 新增！
):
    # 優先檢查兩階段仲裁
    if app_state['use_arbitrator_consensus'] and HAS_ARBITRATOR:
        if not app_state['arbitrator_agent']:
            app_state['arbitrator_agent'] = ArbitratorConsensusAgent()
        
        result = app_state['arbitrator_agent'].analyze_with_arbitration(
            market_data=market_data,
            account_info=account_info,
            position_info=position_info,
            historical_candles=historical_candles,
            successful_cases=successful_cases,
            multi_timeframe_data=multi_timeframe_data  # 新增！
        )
        result['model_type'] = 'arbitrator'
        return result
    # ... 其他模式
```

---

## 📊 資料量統計

### 每次分析 AI 收到：

1. **15m 主時間框架**
   - 當前: 40 種指標
   - 歷史: 20 根 x 40 = 800 數據點

2. **1h 輔助時間框架**
   - 當前: 40 種指標
   - 歷史: 20 根 x 40 = 800 數據點

3. **4h 輔助時間框架**
   - 當前: 40 種指標
   - 歷史: 20 根 x 40 = 800 數據點

4. **成功案例**: 最多 10 個

5. **最近決策**: 5 次

**總計：2500+ 個市場數據點**

---

## ✅ 優勢

1. **看清大趨勢**
   - 15m 可能噪音多
   - 1h + 4h 提供更穩定的趨勢判斷

2. **減少假訊號**
   - 多時間框架確認
   - 提高決策品質

3. **高信心逆勢**
   - 捕捉短線反轉機會
   - 信心度 > 75% 才執行
   - 緊停損 (1-2%)

4. **更全面的市場視野**
   - 3 個時間框架 = 3 個視角
   - AI 可以綜合判斷

---

## 📝 檔案清單

- [x] `core/arbitrator_consensus_agent.py` - 支持多時間框架參數
- [x] `core/multi_timeframe_analyzer.py` - 新增分析器
- [ ] `app_flask.py` - 整合多時間框架分析
- [ ] 測試和驗證

---

## 🔬 測試方法

```python
# 測試多時間框架分析器
from core.realtime_data_loader import RealtimeDataLoader
from core.multi_timeframe_analyzer import MultiTimeframeAnalyzer

data_loader = RealtimeDataLoader()
mt_analyzer = MultiTimeframeAnalyzer(data_loader)

multi_tf_data = mt_analyzer.prepare_multi_timeframe_data(
    symbol='BTCUSDT',
    primary_timeframe='15m',
    secondary_timeframes=['1h', '4h'],
    num_candles=20
)

print("15m 趨勢:", multi_tf_data['15m']['trend'])
print("1h 趨勢:", multi_tf_data['1h']['trend'])
print("4h 趨勢:", multi_tf_data['4h']['trend'])

# 檢查逆勢機會
counter_signal = mt_analyzer.get_counter_trend_signal(multi_tf_data)
if counter_signal['has_signal']:
    print(f"\n🚨 逆勢機會: {counter_signal['direction']}")
    print(f"信心度: {counter_signal['confidence']}%")
    print(f"理由: {counter_signal['reasoning']}")
```

---

## 🌟 核心理念

> **用大時間框架看方向，用小時間框架找進出場**

- 4h 看大趨勢
- 1h 看中期方向
- 15m 找進出場點
- 信心度高時允許逆勢

這樣 AI 就能看清大局，也不會錯過短線機會！🚀
