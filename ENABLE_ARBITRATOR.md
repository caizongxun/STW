# 🚀 啕用兩階段仲裁決策系統

## ⚡ 快速啟用 (3 步驟)

### 1️⃣ 修改配置檔

編輯 `config.json` (如果不存在就建立)：

```json
{
  "use_arbitrator_consensus": true,
  
  "GROQ_API_KEY": "gsk_...",
  "GOOGLE_API_KEY": "AIza...",
  "OPENROUTER_API_KEY": "sk-or-v1-..."
}
```

**核心配置**：
- ✅ `"use_arbitrator_consensus": true` ← **啟用兩階段仲裁**
- ✅ 至少 2 個 API Key (Groq + Google 或 OpenRouter)

---

### 2️⃣ 添加 UI 腳本

編輯 `templates/index.html`，在 `</body>` 標籤**之前**添加：

```html
<!-- 兩階段仲裁 UI -->
<script src="{{ url_for('static', filename='js/arbitrator_ui.js') }}"></script>
</body>
```

---

### 3️⃣ 重啟系統

```bash
# 按 Ctrl+C 停止當前進程

# 重新啟動
python app_flask.py
```

你應該看到：

```
✅ 已配置 8 個 API 提供商 (2026 年 3 月正確模型)
  🚀 Groq_Llama_3_3_70B: llama-3.3-70b-versatile (優先級 5)
  🚀 Google_Gemini_2_Flash: gemini-2.0-flash (優先級 5)
  ✅ OpenRouter_Llama_3_3_70B: meta-llama/llama-3.3-70b-instruct:free (優先級 3)
```

---

## 📊 驗證是否啟用

點擊網頁上的 **「AI 分析」** 按鈕，你應該看到：

```
┌───────────────────────────────────┐
│   🧠 兩階段仲裁決策           │
├───────────────────────────────────┤
│ 階段 1  兩個快速模型分析      │
├─────────────┬─────────────────────┤
│ Model A    │ Model B          │
│ Groq       │ Google Gemini    │
│ OPEN_LONG  │ OPEN_LONG        │
└─────────────┴─────────────────────┘
```

---

## 🛠️ 如果看到單模型？

### 問題 1: `config.json` 不存在

```bash
# 建立配置檔
cp config.example.json config.json

# 編輯 config.json，填入你的 API keys
nano config.json  # 或用任何編輯器
```

確認包含：
```json
{
  "use_arbitrator_consensus": true
}
```

---

### 問題 2: 缺少仲裁檔案

```bash
# 查看是否有這個檔案
ls core/arbitrator_consensus_agent.py

# 如果不存在，重新 pull
git pull origin main
```

---

### 問題 3: app_flask.py 未讀取配置

查看 `app_flask.py` 第 77 行附近：

```python
def load_config():
    if HAS_CONFIG_MANAGER and app_state['config_manager']:
        try:
            config = app_state['config_manager'].load()
            app_state['user_config'] = config
            
            # ✅ 應該有這些
            app_state['use_dual_model'] = config.get('use_dual_model', False)
            app_state['dual_model_mode'] = config.get('dual_model_mode', 'consensus')
```

但是！**兩階段仲裁的讀取在 `/api/analyze` 路由中**，需要添加：

```python
@app.route('/api/analyze', methods=['POST'])
def analyze_market():
    try:
        # ... 前面的代碼 ...
        
        # ✅ 檢查是否使用兩階段仲裁
        use_arbitrator = app_state['user_config'].get('use_arbitrator_consensus', False)
        
        if use_arbitrator:
            from core.arbitrator_consensus_agent import ArbitratorConsensusAgent
            
            agent = ArbitratorConsensusAgent()
            decision = agent.analyze_with_arbitration(
                market_data=latest_data,
                account_info=account_info,
                position_info=position_info
            )
            # ...
```

---

## 📝 完整修改 app_flask.py

在 `/api/analyze` 路由中 (347 行附近)，**在 `decision = _get_ai_decision(...)` 之前**添加：

```python
@app.route('/api/analyze', methods=['POST'])
def analyze_market():
    try:
        data = request.json
        symbol = data.get('symbol', 'BTCUSDT')
        timeframe = data.get('timeframe', '15m')
        auto_log = data.get('auto_log', False)
        
        # ... 獲取市場數據 ...
        
        # ✅ 檢查是否啟用兩階段仲裁
        use_arbitrator = app_state['user_config'].get('use_arbitrator_consensus', False)
        
        if use_arbitrator:
            # 使用兩階段仲裁
            try:
                from core.arbitrator_consensus_agent import ArbitratorConsensusAgent
                
                agent = ArbitratorConsensusAgent()
                result = agent.analyze_with_arbitration(
                    market_data=latest_data,
                    account_info=account_info,
                    position_info=position_info
                )
                
                # 返回詳細結果 (支持 UI 顯示)
                return jsonify({
                    'success': True,
                    'mode': 'arbitrator',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': timestamp.isoformat(),
                    'price': latest_price,
                    'stage_1': {
                        'model_a': result.get('model_a_decision'),
                        'model_b': result.get('model_b_decision'),
                        'agreed': not result.get('needed_arbitration')
                    },
                    'stage_2': {
                        'needed': result.get('needed_arbitration'),
                        'arbitrator': result.get('arbitrator_decision')
                    },
                    'decision': result.get('final_decision')
                })
                
            except ImportError:
                print("⚠️ 未找到 arbitrator_consensus_agent.py，使用單模型")
                # fallback 到單模型
        
        # 原來的單模型或雙模型逻輯
        decision = _get_ai_decision(latest_data, account_info, position_info)
        # ...
```

---

## ✅ 驗證成功

### 終端輸出

```bash
AI 分析嘗試 1/3...
🤖 使用 API: Groq_Llama_3_3_70B (llama-3.3-70b-versatile)
✅ Groq_Llama_3_3_70B 請求成功

🤖 使用 API: Google_Gemini_2_Flash (gemini-2.0-flash)
✅ Google_Gemini_2_Flash 請求成功

⚠️ 意見分歧: OPEN_LONG vs HOLD → 需要仲裁

🧠 使用 API: OpenRouter_Llama_3_3_70B (meta-llama/llama-3.3-70b-instruct:free)
✅ 仲裁者決定: OPEN_LONG (78%)

✅ AI 分析成功: OPEN_LONG (信心度 78%)
[ANALYZE] Model type: arbitrator
```

### 網頁顯示

你會看到紫色游標的兩階段仲裁區塊，顯示：
- 🤖 Model A (Groq Llama 70B)
- 🤖 Model B (Google Gemini 2.0)
- ✅/⚠️ 共識狀態
- 🧠 Arbitrator (如果需要)
- ✅ 最終決策

---

## 💡 常見問題

### Q: 為什麼我沒看到兩階段 UI？

A: 確認以下三點：
1. `config.json` 中 `"use_arbitrator_consensus": true`
2. `templates/index.html` 中有 `<script src=".../arbitrator_ui.js"></script>`
3. 重啟 Flask 系統

### Q: 為什麼還是單模型？

A: 查看 `app_flask.py` 的 `/api/analyze` 路由是否有讀取 `use_arbitrator_consensus` 配置。

### Q: `core/arbitrator_consensus_agent.py` 不存在？

A: 執行 `git pull origin main` 更新代碼。

---

**最後更新**: 2026 年 3 月 7 日 13:36 CST
