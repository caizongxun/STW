# 當前模型數據狀況

## 現在模型收到的資訊

### 1. 40 種技術指標 (OK)

```python
# 越勢指標
ema9, ema21, ema50, ema200
macd, macd_signal, macd_hist
adx

# 動能指標
rsi, stoch_k, stoch_d
cci, mfi, willr

# 波動指標
atr, bb_upper, bb_middle, bb_lower, bb_position

# 成交量
volume_ratio, obv

# 支撐/壓力
dist_to_resistance, dist_to_support
```

### 2. 歷史 K 棒 (X - 缺少)

目前模型**沒有**看到前 20 根 K 棒的：
- open/high/low/close/volume
- 每根 K 棒的時間戳
- K 棒型態（陰線/陽線/上影線/下影線）

### 3. 歷史成功案例 (X - 缺少)

目前模型**沒有**看到 `cases.json` 中的學習案例。

---

## 影響

### 缺少歷史 K 棒

模型無法判斷：
- 趋勢是否反轉
- K 線型態（如錘子、十字星、包含線）
- 短期支撐/壔力的具體位置
- 量能變化趨勢

### 缺少歷史成功案例

模型無法：
- 從過去成功的交易中學習
- 避免重複過去失敗的錯誤
- 參考相似市場狀態的歷史決策

---

## 如何修復

### 方案 A: 修改 `app_flask.py`

在傳給 AI agent 時增加：
```python
# 當前
_get_ai_decision(
    market_data=latest_data,  # 只有 40 指標
    account_info=account_info,
    position_info=position_info
)

# 優化後
_get_ai_decision(
    market_data=latest_data,      # 40 指標
    historical_candles=df.tail(20),  # 歷史 20 根 K 棒
    successful_cases=app_state['cases'],  # 成功案例
    account_info=account_info,
    position_info=position_info
)
```

### 方案 B: 在 `market_features.py` 中增加

在 `prepare_market_features` 函數中直接打包：
```python
def prepare_market_features(row, df):
    # ... 現有 40 指標 ...
    
    # 新增: 歷史 K 棒
    historical_candles = df.tail(20)[[
        'timestamp', 'open', 'high', 'low', 'close', 'volume'
    ]].to_dict('records')
    
    result = {
        # ... 原有指標 ...
        'historical_candles': historical_candles  # 新增
    }
    return result
```

---

## 推薦作法

使用**方案 A**，因為：
1. 不需要修改 `prepare_market_features`
2. 成功案例已經在 `app_state['cases']` 中
3. `df` 已經在 `analyze_market()` 裡了

只需要：
1. 修改 `_get_ai_decision()` 的簽名
2. 更新所有 `ArbitratorConsensusAgent.analyze_with_arbitration()` 的呼叫
3. 在 prompt 中加入歷史 K 棒和成功案例

---

## 是否需要立即修復？

### 當前狀況：
- 40 種指標已經很強了
- 模型可以做基本判斷

### 如果需要更高準確率：
- 需要歷史 K 棒（判斷趋勢和型態）
- 需要成功案例（從歷史學習）

是否現在修復？由你決定。
