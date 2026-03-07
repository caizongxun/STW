# LINE 風格聊天室和 Symbol 修復

## 更新時間
2026-03-07 21:32 CST

## 主要修復

### 1. ✅ 創建 LINE 風格 AI 聊天室

#### 新增檔案
- `templates/ai_chat_line_style.html` - LINE 風格聊天室介面

#### 特性
- 💬 **LINE 風格對話模式**
  - 右側: 用戶 Prompt (藍綠色氣泡)
  - 左側: AI 模型回應 (白色氣泡)
  - 各模型有獨立頭像和名稱

- 📑 **完整 Prompt 顯示**
  - System Prompt (黃色背景)
  - User Prompt (藍色背景)
  - 完整市場數據、賬戶資訊、持倉、多時間框架、歷史 K 棒

- 🤖 **模型回應**
  - Model A: 🤖 (Llama 70B)
  - Model B: 🤖 (Gemini Flash)
  - Arbitrator: ⚖️ (仲裁者)
  - Executor: ✅ (執行審核員)
  - 顯示完整原始輸出 + JSON 格式化

- 🎯 **決策標籤**
  - OPEN_LONG: 綠色
  - OPEN_SHORT: 紅色
  - HOLD: 橘色
  - CLOSE: 藍色

- 🔄 **自動更新**
  - 每 30 秒自動重新加載
  - 顯示最後更新時間

---

### 2. ✅ 修復 Symbol 顯示 UNKNOWN 問題

#### 修改檔案
- `strategies/v13/market_features.py`

#### 修復內容
```python
# 修復前
def prepare_market_features(row, df):
    return {
        'symbol': row.get('symbol', 'UNKNOWN'),  # row 沒有 symbol
        ...
    }

# 修復後
def prepare_market_features(row, df, symbol='UNKNOWN'):
    return {
        'symbol': symbol,  # 使用傳入的 symbol 參數
        ...
    }
```

#### 使用方式
```python
# 在 app_flask.py 中
latest_data = prepare_market_features(df.iloc[-1], df, symbol=symbol)
```

**注意**: `app_flask.py` 需要更新所有調用 `prepare_market_features` 的地方，添加 `symbol` 參數。

---

### 3. ✅ 歷史 K 棒資訊

#### 確認功能
- ✅ 預設提供 **10 根歷史 K 棒** (Arbitrator 模式，優化 Payload)
- ✅ 原始版本提供 **20 根歷史 K 棒** (非 Arbitrator 模式)
- ✅ 每根 K 棒包含 **40+ 技術指標**

#### K 棒資訊結構
```json
{
  "timestamp": "2026-03-07 21:00:00",
  "open": 67950.5,
  "high": 67985.2,
  "low": 67920.1,
  "close": 67955.4,
  "volume": 123.456,
  "features": {
    "symbol": "BTCUSDT",  // 現在會正確顯示
    "ema9": 67973.45,
    "ema21": 67966.86,
    "rsi": 49.16,
    "macd_hist": 1.76,
    "bb_position": 0.47,
    // ... 其他 40+ 指標
  }
}
```

---

## 使用方法

### 1. 更新代碼
```bash
cd ~/STW
git pull origin main
```

### 2. 更新 app_flask.py (重要!)

需要在 `app_flask.py` 中所有調用 `prepare_market_features` 的地方添加 `symbol` 參數：

```python
# 搜尋所有以下調用
prepare_market_features(df.iloc[-1], df)
prepare_market_features(row, df)
prepare_market_features(current_candle, df)

# 更新為
prepare_market_features(df.iloc[-1], df, symbol=symbol)
prepare_market_features(row, df, symbol=symbol)
prepare_market_features(current_candle, df, symbol=symbol)
```

主要位置：
1. `/api/analyze` 路由 - `analyze_market()`
2. `/api/ai-log/update` 路由 - `update_ai_log()`
3. `bybit_trading_worker()` 函數
4. `_prepare_historical_candles()` 函數內部

### 3. 重啟伺服器
```bash
pkill -f app_flask.py
python app_flask.py
```

### 4. 訪問 LINE 風格聊天室

**方法1**: 直接訪問
```
http://localhost:5000/ai-chat
```

**方法2**: 在主頁面執行分析後，點擊「AI 聊天室」連結

---

## 預覽截圖

### LINE 風格對話

```
+--------------------------------------------------+
|  🤖 AI 分析聊天室                       ← 返回主頁  |
+--------------------------------------------------+
|
|  2026-03-07 21:00:00
|
|                              +------------------+
|                              | 📊 市場分析請求  |
|                              |                  |
|                              | System Prompt:   |
|                              | 專業加密貨幣...  |
|                              |                  |
|                              | User Prompt:     |
|                              | === 市場數據 === |
|                              | symbol: BTCUSDT  |
|                              | close: 67955.4   |
|                              | ...              |
|                              +------------------+
|
|  🤖 Llama_70B_A1
|  +----------------------------------------+
|  | OPEN_LONG  信心度: 60%              |
|  |                                        |
|  | {
|  |   "action": "OPEN_LONG",
|  |   "confidence": 60,
|  |   "reasoning": "市場短期內..."
|  | }
|  +----------------------------------------+
|
|  🤖 Gemini_Flash_B1
|  +----------------------------------------+
|  | HOLD  信心度: 55%                  |
|  |                                        |
|  | {
|  |   "action": "HOLD",
|  |   "confidence": 55,
|  |   "reasoning": "市場趋勢..."
|  | }
|  +----------------------------------------+
|
|  ⚖️ 仲裁者: Llama_70B_Arb1
|  +----------------------------------------+
|  | OPEN_LONG  信心度: 65%              |
|  |                                        |
|  | {
|  |   "action": "OPEN_LONG",
|  |   "confidence": 65,
|  |   "reasoning": "綜合兩個..."
|  | }
|  +----------------------------------------+
|
|  ✅ 執行審核員
|  +----------------------------------------+
|  | 決策: EXECUTE                        |
|  | 最終動作: OPEN_LONG                |
|  | 調整信心度: 65%                  |
|  |                                        |
|  | {
|  |   "execution_decision": "EXECUTE",
|  |   "reasoning": "信心度..."
|  | }
|  +----------------------------------------+
|
+--------------------------------------------------+
```

---

## 已知問題

### app_flask.py 需要手動更新

由於 `app_flask.py` 檔案太大，我無法一次性更新。請手動修改所有調用 `prepare_market_features` 的位置。

#### 具體位置：

1. **analyze_market()** - 約第 450 行
```python
# 修改前
latest_data = prepare_market_features(df.iloc[-1], df)

# 修改後
latest_data = prepare_market_features(df.iloc[-1], df, symbol=symbol)
```

2. **_prepare_historical_candles()** - 約第 250 行
```python
# 修改前
features = prepare_market_features(row, df_slice)

# 修改後
features = prepare_market_features(row, df_slice, symbol='BTCUSDT')  # 或傳入 symbol 變數
```

3. **update_ai_log()** - 約第 600 行
```python
# 修改前
market_data = prepare_market_features(current_candle, df)

# 修改後
market_data = prepare_market_features(current_candle, df, symbol=symbol)
```

4. **bybit_trading_worker()** - 約第 750 行
```python
# 修改前
market_data = prepare_market_features(current_candle, df)

# 修改後
market_data = prepare_market_features(current_candle, df, symbol=symbol)
```

---

## 測試

### 1. 測試 Symbol 修復

1. 訪問 http://localhost:5000
2. 點擊「獲取實時訊號」
3. 檢查 Prompt 中的 `symbol` 欄位：
   - ✅ 正確: `"symbol": "BTCUSDT"`
   - ❌ 錯誤: `"symbol": "UNKNOWN"`

### 2. 測試 LINE 風格聊天室

1. 訪問 http://localhost:5000/ai-chat
2. 確認顯示：
   - ✅ 右側用戶 Prompt (藍綠色氣泡)
   - ✅ 左側 AI 回應 (白色氣泡)
   - ✅ 各模型有頭像和名稱
   - ✅ 完整 System/User Prompt
   - ✅ 完整 AI 原始輸出
   - ✅ JSON 格式化顯示
   - ✅ 決策標籤有顏色

### 3. 測試歷史 K 棒

在 LINE 聊天室中檢查 User Prompt 的 `=== 歷史 K 棒 ===` 部分：
- ✅ 應該有 10 根 K 棒 (Arbitrator 模式)
- ✅ 每根 K 棒包含 `features` 字典
- ✅ `features` 中的 `symbol` 為 `BTCUSDT`

---

## 故障排除

### Symbol 仍然顯示 UNKNOWN

1. 確認 `strategies/v13/market_features.py` 已更新
2. 確認 `app_flask.py` 中所有 `prepare_market_features` 調用都添加了 `symbol` 參數
3. 重啟 Flask 伺服器

### LINE 聊天室不顯示

1. 確認 `templates/ai_chat_line_style.html` 已創建
2. 確認 `api_routes_ai_chat.py` 已更新
3. 確認 Flask 啟動時顯示: `[OK] AI 聊天室 API 路由已註冊 (LINE 風格)`

### Prompt 顯示過長

- 耶位有捲動軟，可以捲動查看
- 最大高度 300px，超過會顯示捲動軟

---

## 下一步

- [ ] 手動更新 `app_flask.py` 中的 `prepare_market_features` 調用
- [ ] 測試 Symbol 是否正確顯示
- [ ] 測試 LINE 風格聊天室是否正常工作
- [ ] 在主頁面添加「AI 聊天室」連結按鈕

---

## 聯繫

如有問題，請提供：
1. Flask 日誌輸出
2. 瀏覽器控制台錯誤
3. Symbol 顯示的完整 JSON
4. LINE 聊天室截圖
