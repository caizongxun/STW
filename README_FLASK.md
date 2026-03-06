# STW - Flask 版 AI 交易系統

## 🌟 為什麼要改用 Flask？

### Streamlit 的問題：
1. ❗ **頁面重新載入**：每次更新都會刷新整個頁面，造成閃爍
2. ❗ **無法多 Tab 同時操作**：一個 Tab 更新時，其他 Tab 全部凍結
3. ❗ **狀態管理困難**：每次重新載入都會丟失狀態
4. ❗ **無法真正即時更新**：需要不斷 `st.rerun()`

### Flask 的優勢：
1. ✅ **真正的即時更新**：WebSocket 推送，無需重新載入
2. ✅ **多 Tab 同時運作**：每個 Tab 獨立運作
3. ✅ **狀態持久化**：服務端管理狀態
4. ✅ **更好的使用體驗**：無閃爍、流暢

---

## 🚀 快速開始

### 1. 安裝依賴

```bash
cd C:\Users\zong\PycharmProjects\STW
pip install -r requirements_flask.txt
```

### 2. 啟動服務

```bash
python app_flask.py
```

### 3. 開啟瀏覽器

訪問：[http://localhost:5000](http://localhost:5000)

---

## 💻 功能特色

### ✨ 已完成功能

1. **[📊 SIGNAL] 實時訊號 & 回測**
   - AI 分析市場訊號
   - 回測績效評估
   - 無頁面重新載入

2. **[📝 AI LOG] AI 預測記錄**
   - 記錄每根 K 棒的 AI 預測
   - 自動計算準確率
   - 支持自動更新 (每 5 秒)
   - CSV 導出
   - 即時統計資訊

3. **WebSocket 即時通訊**
   - 即時推送 AI 訊號
   - 即時更新預測記錄
   - 連線狀態監控

### 🚧 開發中功能

- [⏰ AUTO] 自動交易
- [💰 BYBIT] Bybit Demo 交易
- [📚 CASES] 學習案例庫
- [⚙️ CONFIG] 系統設定

---

## 📚 API 路由

### 分析與回測

```http
POST /api/analyze
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "timeframe": "15m"
}
```

```http
POST /api/backtest
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "timeframe": "15m",
  "capital": 10000,
  "simulation_days": 30,
  "ai_confidence_threshold": 0.7
}
```

### AI 預測記錄

```http
GET /api/ai-log/get
```

```http
POST /api/ai-log/update
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "timeframe": "15m"
}
```

```http
POST /api/ai-log/clear
```

### WebSocket 事件

```javascript
// 連接
socket.on('connect', () => {
  console.log('Connected');
});

// 訊號更新
socket.on('signal_updated', (data) => {
  console.log('New signal:', data);
});

// AI 記錄更新
socket.on('ai_log_updated', (data) => {
  console.log('AI log updated:', data);
});
```

---

## 📝 檔案結構

```
STW/
├── app_flask.py           # Flask 主程式
├── app.py                 # Streamlit 舊版 (保留)
├── requirements_flask.txt # Flask 依賴
├── static/
│   ├── css/
│   │   └── style.css     # 自訂樣式
│   └── js/
│       ├── main.js       # 主邏輯
│       └── ai_log.js     # AI 記錄邏輯
├── templates/
│   └── index.html        # 主頁面
├── core/                 # 核心邏輯 (保持不變)
│   ├── data_loader.py
│   ├── llm_agent_position_aware.py
│   └── ...
└── strategies/           # 策略模塊 (保持不變)
    └── v13/
        ├── __init__.py
        ├── market_features.py
        └── ...
```

---

## ⚙️ 配置說明

### 修改連接埠

預設：`http://localhost:5000`

修改 `app_flask.py` 最後一行：

```python
socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

### 啟用生產模式

```bash
gunicorn --worker-class eventlet -w 1 app_flask:app --bind 0.0.0.0:5000
```

---

## 🔧 開發說明

### 添加新功能

1. **後端 API**：在 `app_flask.py` 新增路由
2. **前端 UI**：在 `templates/index.html` 新增 Tab
3. **JavaScript**：在 `static/js/` 建立新檔案

### 保持模塊化

- `core/`：核心邏輯不更動
- `strategies/`：策略模塊不更動
- 只更改了顯示層 (Flask + HTML + JS)

---

## 📊 效能比較

| 項目 | Streamlit | Flask |
|------|-----------|-------|
| 頁面重新載入 | ✅ 每次更新 | ❌ 無需重載 |
| 多 Tab 同時操作 | ❌ 不支持 | ✅ 支持 |
| 即時更新 | ❌ 假性 | ✅ 真性 |
| 狀態管理 | ❌ 難管理 | ✅ 持久化 |
| 開發速度 | ✅ 快 | ⏸️ 中 |
| UI 彈性 | ❌ 固定 | ✅ 完全自訂 |

---

## 🐛 問題排除

### 1. WebSocket 連接失敗

確認 `eventlet` 已安裝：

```bash
pip install eventlet
```

### 2. CORS 錯誤

已啟用 `Flask-CORS`，如果還有問題修改：

```python
CORS(app, resources={r"/*": {"origins": "*"}})
```

### 3. AI 模型未啟動

確認 Ollama 正在運行：

```bash
curl http://localhost:11434
```

---

## 📦 部署

### Docker 部署

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements_flask.txt .
RUN pip install -r requirements_flask.txt

COPY . .

EXPOSE 5000

CMD ["python", "app_flask.py"]
```

### 生產環境

使用 Gunicorn + Nginx：

```bash
gunicorn --worker-class eventlet -w 1 app_flask:app --bind 0.0.0.0:5000
```

---

## 📝 更新記錄

### v1.0 (2026-03-06)

- ✅ 完成 Flask 架構轉換
- ✅ WebSocket 即時通訊
- ✅ AI 預測記錄功能
- ✅ 實時訊號 & 回測
- ✅ 無頁面重新載入

---

## 👥 貢獻

歡迎 PR 和 Issue！

---

## 📝 License

MIT License
