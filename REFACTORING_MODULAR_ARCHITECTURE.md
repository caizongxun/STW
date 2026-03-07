# 模塊化重構說明

## 更新時間
2026-03-07 21:41 CST

## 重構目標

✅ 將龐大的 `app_flask.py` (約 1000+ 行) 拆分成多個模塊  
✅ 修復所有 `prepare_market_features` 調用中的 `symbol` 問題  
✅ 保持原有功能完全不變  
✅ 提高代碼可維護性和可讀性  

---

## 模塊化結構

### 原始結構
```
STW/
├── app_flask.py          (≈ 1000+ 行，所有功能集中在一個檔案)
├── core/
│   ├── ...
│   └── arbitrator_consensus_agent.py
├── strategies/
│   └── v13/
│       └── market_features.py
└── templates/
    └── index.html
```

### 新的模塊化結構
```
STW/
├── app_flask.py                      (≈ 200 行，只負責啟動和路由註冊)
├── routes/                           (新增 - 路由模塊)
│   ├── config_routes.py              (配置管理路由)
│   ├── analysis_routes.py            (AI 分析、回測路由)
│   └── trading_routes.py             (Bybit 交易、案例管理路由)
├── core/
│   ├── config_utils.py               (新增 - 配置工具)
│   ├── ai_log_utils.py               (新增 - AI 日誌工具)
│   ├── websocket_handlers.py         (新增 - WebSocket 處理)
│   ├── ...
│   └── arbitrator_consensus_agent.py
├── strategies/
│   └── v13/
│       └── market_features.py        (已修改 - 添加 symbol 參數)
└── templates/
    ├── index.html
    └── ai_chat_line_style.html       (新增 - LINE 風格聊天室)
```

---

## 模塊說明

### 1. `app_flask.py` - 主程式 (≈ 200 行)

**負責**:
- Flask 應用初始化
- 路由註冊
- 啟動伺服器
- 功能模塊載入

**主要程式碼**:
```python
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS

# 導入模塊化路由
from routes.config_routes import register_config_routes
from routes.analysis_routes import register_analysis_routes
from routes.trading_routes import register_trading_routes
from core.config_utils import load_config, load_cases
from core.websocket_handlers import register_websocket_handlers

app = Flask(__name__)
socketio = SocketIO(app)

# 註冊路由
register_config_routes(app, app_state, config_manager, HAS_CONFIG_MANAGER)
register_analysis_routes(app, app_state)
register_trading_routes(app, app_state)
register_websocket_handlers(socketio, app_state)

socketio.run(app, host='0.0.0.0', port=5000)
```

---

### 2. `routes/config_routes.py` - 配置管理路由

**負責**:
- `/api/config/get` - 獲取配置
- `/api/config/save` - 保存配置
- `/api/config/reset` - 重設配置
- `/api/config/test-apis` - 測試 API 鍵
- `/api/config/api-stats` - API 統計

**功能**:
- API Key 管理
- 模型選擇配置
- 多 API 管理

---

### 3. `routes/analysis_routes.py` - 分析路由 (★ 核心修復)

**負責**:
- `/api/analyze` - AI 分析市場
- `/api/backtest` - 回測
- `/api/ai-log/update` - 更新 AI 日誌
- `/api/ai-log/clear` - 清除日誌
- `/api/ai-log/get` - 獲取日誌
- `/api/arbitrator/stats` - 仲裁者統計
- `/api/dual-model/stats` - 雙模型統計

**修復**:
✅ 所有 `prepare_market_features` 調用都添加 `symbol` 參數

```python
# 修復前
latest_data = prepare_market_features(df.iloc[-1], df)

# 修復後
latest_data = prepare_market_features(df.iloc[-1], df, symbol=symbol)
```

**內部函數**:
- `_prepare_historical_candles(df, symbol, num_candles)` - 準備歷史 K 棒
- `_get_ai_decision(app_state, ...)` - 獲取 AI 決策

---

### 4. `routes/trading_routes.py` - 交易路由

**負責**:
- `/api/bybit/test` - 測試 Bybit 連接
- `/api/cases/list` - 案例列表
- `/api/cases/add` - 添加案例
- `/api/cases/delete/<case_id>` - 刪除案例

**功能**:
- Bybit Demo 交易管理
- 成功案例庫管理

---

### 5. `core/config_utils.py` - 配置工具

**功能**:
- `load_config(app_state, config_manager, HAS_CONFIG_MANAGER)` - 載入配置
- `save_config(app_state, config_manager, config, HAS_CONFIG_MANAGER)` - 保存配置
- `load_cases(app_state)` - 載入案例
- `save_cases(app_state)` - 保存案例

**檔案**:
- `config.json` - 配置檔
- `cases.json` - 案例檔

---

### 6. `core/ai_log_utils.py` - AI 日誌工具

**功能**:
- `save_ai_prediction_log(...)` - 保存 AI 預測日誌
- `_get_direction_from_action(action)` - 獲取方向
- `_update_previous_log_accuracy(logs, current_price)` - 更新準確率

**資訊**:
- 動作 (OPEN_LONG, OPEN_SHORT, HOLD, CLOSE)
- 信心度
- 模型類型 (single, dual, arbitrator)
- 執行決策 (EXECUTE, REJECT, REDUCE_SIZE)
- 預測準確率

---

### 7. `core/websocket_handlers.py` - WebSocket 處理 (★ 修復)

**負責**:
- `@socketio.on('connect')` - 客戶端連接
- `@socketio.on('disconnect')` - 客戶端斷開
- `@socketio.on('start_bybit_trading')` - 啟動自動交易
- `@socketio.on('stop_bybit_trading')` - 停止自動交易
- `bybit_trading_worker(socketio, app_state, config)` - 交易工作線程

**修復**:
✅ `bybit_trading_worker` 中所有 `prepare_market_features` 調用都添加 `symbol` 參數

```python
# 修復前
market_data = prepare_market_features(current_candle, df)

# 修復後
market_data = prepare_market_features(current_candle, df, symbol=symbol)
```

---

### 8. `strategies/v13/market_features.py` - 市場特徵 (★ 修復)

**修改**:
```python
# 修復前
def prepare_market_features(row, df):
    return {
        'symbol': row.get('symbol', 'UNKNOWN'),  # ✖️ row 沒有 symbol
        'close': float(row['close']),
        ...
    }

# 修復後
def prepare_market_features(row, df, symbol='UNKNOWN'):
    return {
        'symbol': symbol,  # ✅ 使用傳入的 symbol 參數
        'close': float(row['close']),
        ...
    }
```

**影響**:
- 現在 `symbol` 會正確顯示為 `BTCUSDT`
- 不再顯示 `UNKNOWN`

---

## 修復清單

### Symbol 問題修復位置

✅ **1. `strategies/v13/market_features.py`**
   - 添加 `symbol` 參數到 `prepare_market_features` 函數

✅ **2. `routes/analysis_routes.py`**
   - 第 45 行: `_prepare_historical_candles` 函數內
   - 第 130 行: `/api/analyze` 路由
   - 第 265 行: `/api/ai-log/update` 路由

✅ **3. `core/websocket_handlers.py`**
   - 第 70 行: `bybit_trading_worker` 函數

---

## 使用方法

### 1. 更新代碼
```bash
cd ~/STW
git pull origin main
```

### 2. 確認新檔案存在
```bash
ls routes/
# 應該有: config_routes.py  analysis_routes.py  trading_routes.py

ls core/ | grep utils
# 應該有: config_utils.py  ai_log_utils.py  websocket_handlers.py
```

### 3. 重啟伺服器
```bash
pkill -f app_flask.py
python app_flask.py
```

### 4. 檢查啟動輸出
```
=============================================================
  Flask Server Starting - STW AI Trading System
=============================================================
  Features:
    ...
    - Modular architecture (routes separated)       # 新增
    ...
  Symbol Fix: All prepare_market_features calls   # 新增
              include symbol parameter
=============================================================
```

---

## 測試

### 1. 測試 Symbol 修復

**步驟**:
1. 訪問 http://localhost:5000
2. 點擊「獲取實時訊號」
3. 檢查結果

**預期結果**:
```json
{
  "symbol": "BTCUSDT",  // ✅ 不是 "UNKNOWN"
  "close": 67955.4,
  "ema9": 67973.45,
  ...
}
```

### 2. 測試 LINE 風格聊天室

**步驟**:
1. 訪問 http://localhost:5000/ai-chat
2. 檢查顯示

**預期結果**:
- ✅ 右側: 用戶 Prompt (藍綠色氣泡)
- ✅ 左側: AI 回應 (白色氣泡)
- ✅ 完整 System/User Prompt
- ✅ 所有模型的完整輸出
- ✅ Prompt 中 `symbol` 顯示為 `BTCUSDT`

### 3. 測試模塊化功能

**檢查路由**:
```bash
# 配置管理
curl http://localhost:5000/api/config/get

# AI 分析
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "timeframe": "15m"}'

# 案例列表
curl http://localhost:5000/api/cases/list

# AI 聊天室
curl http://localhost:5000/api/ai-chat-data
```

---

## 優勢

### 1. 可維護性 ⬆️
- 每個檔案只負責一個功能領域
- 代碼量從 1000+ 行減少到 200 行
- 更容易找到需要修改的代碼

### 2. 可讀性 ⬆️
- 清晰的檔案結構
- 每個檔案有明確的責任區分
- 函數名稱更有意義

### 3. 可測試性 ⬆️
- 每個模塊可獨立測試
- 更容易寫單元測試

### 4. 可擴展性 ⬆️
- 添加新功能只需創建新模塊
- 不會影響現有功能

### 5. 協作 ⬆️
- 多人可以同時修改不同模塊
- 減少 Git 衝突

---

## 文件大小比較

| 檔案 | 修改前 | 修改後 |
|------|---------|----------|
| `app_flask.py` | 1000+ 行 | 200 行 |
| `routes/config_routes.py` | - | 150 行 |
| `routes/analysis_routes.py` | - | 450 行 |
| `routes/trading_routes.py` | - | 80 行 |
| `core/config_utils.py` | - | 100 行 |
| `core/ai_log_utils.py` | - | 130 行 |
| `core/websocket_handlers.py` | - | 150 行 |

**總計**: 1 個大檔案 → 7 個小模塊

---

## 內部相依關係

```
app_flask.py
├── routes/config_routes.py
│   └── core/config_utils.py
│       └── core/config_manager.py
├── routes/analysis_routes.py
│   ├── strategies/v13/market_features.py
│   ├── core/ai_log_utils.py
│   ├── core/realtime_data_loader.py
│   └── core/arbitrator_consensus_agent.py
├── routes/trading_routes.py
│   ├── core/bybit_trader.py
│   └── core/config_utils.py
└── core/websocket_handlers.py
    ├── strategies/v13/market_features.py
    └── routes/analysis_routes.py
```

---

## 故障排除

### 問題 1: `ModuleNotFoundError: No module named 'routes'`

**原因**: `routes/` 目錄不存在或缺少 `__init__.py`

**解決**:
```bash
mkdir -p routes
touch routes/__init__.py
```

### 問顏 2: Symbol 仍然顯示 "UNKNOWN"

**原因**: 舊版本的 `market_features.py` 或 Python 快取

**解決**:
```bash
# 1. 確認檔案已更新
git pull origin main

# 2. 清除 Python 快取
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete

# 3. 重啟
pkill -f app_flask.py
python app_flask.py
```

### 問題 3: 路由不工作 (404 Not Found)

**原因**: 路由模塊未正確註冊

**解決**:
1. 檢查 `app_flask.py` 是否有調用 `register_*_routes`
2. 檢查啟動輸出是否有 `[OK]` 訊息

---

## 下一步優化建議

1. **增加單元測試**
   - 為每個模塊編寫測試
   - 使用 `pytest` 框架

2. **添加類型提示**
   - 使用 Python Type Hints
   - 增加代碼可讀性和 IDE 支持

3. **錯誤處理增強**
   - 統一錯誤處理機制
   - 添加更詳細的錯誤日誌

4. **模塊文檔**
   - 每個模塊添加詳細 docstring
   - 創建 API 文檔

5. **配置模塊化**
   - 將 `app_state` 抽離成獨立模塊
   - 使用配置類別管理狀態

---

## 總結

✅ **成功完成模塊化重構**
- 1 個 1000+ 行的大檔案 → 7 個小模塊
- 保持所有原有功能
- 提高代碼質量和可維護性

✅ **修復 Symbol 問題**
- 所有 `prepare_market_features` 調用都添加 `symbol` 參數
- `symbol` 不再顯示 "UNKNOWN"

✅ **增加 LINE 風格聊天室**
- 對話模式顯示完整 Prompt 和 AI 回應
- 更直觀的 UI 設計

---

## 相關文檔

- [BUGFIX_GEMINI_AND_AI_CHAT.md](./BUGFIX_GEMINI_AND_AI_CHAT.md) - Gemini API 修復
- [UPDATE_LINE_CHAT_AND_SYMBOL_FIX.md](./UPDATE_LINE_CHAT_AND_SYMBOL_FIX.md) - LINE 聊天室和 Symbol 修復
- [REFACTORING_MODULAR_ARCHITECTURE.md](./REFACTORING_MODULAR_ARCHITECTURE.md) - 本文檔

---

如有任何問題，請提供詳細的錯誤訊息和日誌輸出。
