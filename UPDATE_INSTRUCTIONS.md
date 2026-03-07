# 更新說明 - Prompt 和模型回應顯示

## ✅ 已完成所有後端修正

### 1. 修正 `core/arbitrator_consensus_agent.py`

✅ **修正 Prompt 加入歷史 K 棒和成功案例**
- `_prepare_prompts()` 現在會包含 `historical_candles` (前 20 根 K 棒的 **40 種技術指標**)
- 加入 `successful_cases` (最多 10 個成功案例)
- 加入 `recent_decisions` (最近 5 次決策)

✅ **記錄詳細分析過程**
- 新增 `self.last_analysis_detail` 字典記錄：
  - `system_prompt`: 系統 prompt
  - `user_prompt`: 使用者 prompt (包含 20 根 K 棒 x 40 指標)
  - `model_responses`: 3 個模型的完整回應
    - `model_a`: Model A 的回應
    - `model_b`: Model B 的回應  
    - `arbitrator`: 仲裁者的回應
  - `final_decision`: 最終決策

✅ **新增 API 方法**
- `get_last_analysis_detail()`: 獲取最近一次的詳細分析

---

### 2. 新增 `api_routes_analysis_detail.py`

✅ **建立 API 路由**
- `GET /api/analysis-detail/latest`: 獲取最近一次分析的詳細資訊
- `GET /api/analysis-detail/export`: 匯出分析詳細為 JSON 檔案

---

### 3. ✅ 更新 `app_flask.py`

✅ **已加入 API 註冊**
```python
# 導入分析詳細 API 路由
try:
    from api_routes_analysis_detail import register_analysis_detail_routes
    HAS_ANALYSIS_DETAIL = True
except ImportError as e:
    HAS_ANALYSIS_DETAIL = False
    print(f"警告: 分析詳細功能不可用 - {e}")

# 在 if __name__ == '__main__': 區塊
if HAS_ANALYSIS_DETAIL:
    register_analysis_detail_routes(app, app_state)
    print("✅ 分析詳細功能已啟用")
```

✅ **修正 `_prepare_historical_candles()` 函數**
- 現在對 **每一根 K 棒** 都使用 `prepare_market_features()` 計算完整的40種技術指標
- 每根 K 棒包含：
  - 基本 OHLCV
  - 趨勢指標：EMA9, EMA21, EMA50, EMA200, MACD, ADX
  - 動能指標：RSI, Stochastic, CCI, MFI, Williams %R
  - 波動指標：ATR, 布林帶 (upper/middle/lower/position)
  - 成交量指標：Volume Ratio, OBV
  - 支撐/壓力：Pivot, Resistance, Support

---

## 現在 AI 收到的完整資訊

### User Prompt 範例：

```
=== 市場數據 ===
當前價格: $50000
RSI: 45.2
MACD: 12.5
... (所有40種指標)

=== 歷史 K 棒 (前 20 根，每根含 40 種指標) ===
[
  {
    "timestamp": "2026-03-07 18:00:00",
    "open": 50000,
    "high": 50500,
    "low": 49800,
    "close": 50200,
    "volume": 1234.5,
    "features": {
      "close": 50200,
      "ema9": 50150,
      "ema21": 50100,
      "ema50": 50050,
      "ema200": 49800,
      "macd": 12.5,
      "macd_signal": 10.2,
      "macd_hist": 2.3,
      "adx": 25.8,
      "rsi": 45.2,
      "stoch_k": 42.1,
      "stoch_d": 40.5,
      "cci": 15.3,
      "mfi": 55.7,
      "willr": -52.3,
      "atr": 1250.5,
      "bb_upper": 51000,
      "bb_middle": 50000,
      "bb_lower": 49000,
      "bb_position": 0.6,
      "volume_ratio": 1.2,
      "obv": 123456789,
      "dist_to_resistance": 1.5,
      "dist_to_support": 0.8
    }
  },
  ... (共 20 根 K 棒)
]

=== 最近 5 次決策 ===
[...]

=== 成功案例 (共 10 個) ===
[...]
```

---

## 🔍 如何查看 Prompt 和模型回應

### 方法 1: API 呼叫
```bash
# 獲取最新分析詳情
curl http://localhost:5000/api/analysis-detail/latest

# 匯出為 JSON 檔案
curl http://localhost:5000/api/analysis-detail/export -o analysis.json
```

### 方法 2: 前端顯示 (需要完成)

---

## 📝 需要完成的前端功能

### 4. 前端顯示功能

需要在前端 (HTML/JavaScript) 加入顯示功能：

#### 建議加入以下功能：

1. **實時預測 Tab 中加入「查看 Prompt 詳細」按鈕**
   - 點擊後顯示 Modal 視窗
   - 顯示 System Prompt
   - 顯示 User Prompt (包含 20 根 K 棒 x 40 指標)
   - 顯示 3 個模型的完整回應

2. **JavaScript 程式碼範例**

```javascript
// 獲取分析詳細
function showAnalysisDetail() {
    fetch('/api/analysis-detail/latest')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const detail = data.detail;
                
                // 顯示 Modal
                const modal = document.createElement('div');
                modal.className = 'modal';
                modal.innerHTML = `
                    <div class="modal-content" style="max-width: 90%; max-height: 90vh; overflow-y: auto;">
                        <span class="close" onclick="this.parentElement.parentElement.remove()">&times;</span>
                        
                        <h3>📊 Prompt 詳細資訊</h3>
                        <p><strong>時間:</strong> ${detail.timestamp}</p>
                        
                        <div class="prompt-section">
                            <h4>📢 System Prompt</h4>
                            <pre class="prompt-content">${detail.prompts.system_prompt}</pre>
                        </div>
                        
                        <div class="prompt-section">
                            <h4>📝 User Prompt</h4>
                            <div class="accordion">
                                <button class="accordion-btn" onclick="toggleAccordion(this)">
                                    查看完整 User Prompt (包含 20 根 K 棒 x 40 指標)
                                </button>
                                <div class="accordion-content" style="display: none;">
                                    <pre class="prompt-content">${detail.prompts.user_prompt}</pre>
                                </div>
                            </div>
                        </div>
                        
                        <div class="model-response-section">
                            <h4>🤖 Model A 回應</h4>
                            <p><strong>模型:</strong> ${detail.model_responses.model_a.model_name}</p>
                            <p><strong>決策:</strong> <span class="badge">${detail.model_responses.model_a.action}</span></p>
                            <p><strong>信心度:</strong> ${detail.model_responses.model_a.confidence}%</p>
                            <div class="accordion">
                                <button class="accordion-btn" onclick="toggleAccordion(this)">
                                    查看完整回應
                                </button>
                                <div class="accordion-content" style="display: none;">
                                    <pre class="response-content">${detail.model_responses.model_a.full_response}</pre>
                                </div>
                            </div>
                        </div>
                        
                        <div class="model-response-section">
                            <h4>🤖 Model B 回應</h4>
                            <p><strong>模型:</strong> ${detail.model_responses.model_b.model_name}</p>
                            <p><strong>決策:</strong> <span class="badge">${detail.model_responses.model_b.action}</span></p>
                            <p><strong>信心度:</strong> ${detail.model_responses.model_b.confidence}%</p>
                            <div class="accordion">
                                <button class="accordion-btn" onclick="toggleAccordion(this)">
                                    查看完整回應
                                </button>
                                <div class="accordion-content" style="display: none;">
                                    <pre class="response-content">${detail.model_responses.model_b.full_response}</pre>
                                </div>
                            </div>
                        </div>
                        
                        ${detail.model_responses.arbitrator ? `
                            <div class="model-response-section">
                                <h4>⚖️ 仲裁者回應</h4>
                                <p><strong>模型:</strong> ${detail.model_responses.arbitrator.model_name}</p>
                                <p><strong>決策:</strong> <span class="badge">${detail.model_responses.arbitrator.action}</span></p>
                                <p><strong>信心度:</strong> ${detail.model_responses.arbitrator.confidence}%</p>
                                <div class="accordion">
                                    <button class="accordion-btn" onclick="toggleAccordion(this)">
                                        查看完整回應
                                    </button>
                                    <div class="accordion-content" style="display: none;">
                                        <pre class="response-content">${detail.model_responses.arbitrator.full_response}</pre>
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                        
                        <div class="final-decision-section">
                            <h4>✅ 最終決策</h4>
                            <pre>${JSON.stringify(detail.final_decision, null, 2)}</pre>
                        </div>
                        
                        <div class="button-group">
                            <button class="btn-export" onclick="exportAnalysisDetail()">💾 匯出 JSON</button>
                            <button class="btn-close" onclick="this.parentElement.parentElement.parentElement.remove()">關閉</button>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            } else {
                alert('無法獲取分析詳情: ' + (data.error || '未知錯誤'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('請求失敗');
        });
}

// 折疊功能
function toggleAccordion(btn) {
    const content = btn.nextElementSibling;
    if (content.style.display === 'none') {
        content.style.display = 'block';
        btn.textContent = btn.textContent.replace('查看', '隱藏');
    } else {
        content.style.display = 'none';
        btn.textContent = btn.textContent.replace('隱藏', '查看');
    }
}

// 匯出 JSON
function exportAnalysisDetail() {
    window.open('/api/analysis-detail/export', '_blank');
}
```

3. **CSS 樣式**

```css
.modal {
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.7);
    display: flex;
    justify-content: center;
    align-items: center;
}

.modal-content {
    background-color: #1e1e1e;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    color: #fff;
    position: relative;
}

.close {
    position: absolute;
    right: 20px;
    top: 20px;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
}

.close:hover {
    color: #ff4444;
}

.prompt-section, .model-response-section, .final-decision-section {
    margin: 20px 0;
    padding: 15px;
    background-color: #2a2a2a;
    border-radius: 5px;
}

.prompt-content, .response-content {
    background-color: #1a1a1a;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: 400px;
    overflow-y: auto;
}

.accordion-btn {
    background-color: #3a3a3a;
    color: white;
    cursor: pointer;
    padding: 10px;
    width: 100%;
    border: none;
    text-align: left;
    outline: none;
    border-radius: 5px;
    margin: 10px 0;
}

.accordion-btn:hover {
    background-color: #4a4a4a;
}

.badge {
    background-color: #28a745;
    padding: 5px 10px;
    border-radius: 3px;
    font-weight: bold;
}

.button-group {
    margin-top: 20px;
    display: flex;
    gap: 10px;
}

.btn-export, .btn-close {
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
}

.btn-export {
    background-color: #007bff;
    color: white;
}

.btn-close {
    background-color: #6c757d;
    color: white;
}
```

---

## 檔案更新清單

- [x] `core/arbitrator_consensus_agent.py` - 修正 prompt 加入歷史資料
- [x] `api_routes_analysis_detail.py` - 新增 API 路由
- [x] `app_flask.py` - 註冊新 API + 修正 _prepare_historical_candles
- [ ] `templates/index.html` - 前端顯示功能
- [ ] CSS 樣式 - Modal 視窗樣式

---

## 测试方法

```bash
# 测试 API
curl http://localhost:5000/api/analysis-detail/latest

# 匯出 JSON
curl http://localhost:5000/api/analysis-detail/export -o analysis_detail.json
```

---

## 使用方式

1. 啟動系統：`python app_flask.py`
2. 在實時預測介面點擊「分析市場」
3. 分析完成後，點擊「查看 Prompt 詳細」按鈕
4. 即可看到：
   - 完整的 System Prompt
   - 完整的 User Prompt (包含 **20 根 K 棒 x 40 種技術指標**)
   - Model A 的完整回應
   - Model B 的完整回應
   - 仲裁者的完整回應 (如果有的話)

---

## 🌟 主要改進

1. **完整的市場資訊**: 每根 K 棒包含 40 種技術指標
2. **歷史資料丰富**: 20 根 K 棒 = 20 x 40 = 800 個數據點
3. **學習案例**: 最多 10 個成功案例
4. **決策歷史**: 最近 5 次決策記錄
5. **完整記錄**: 所有 prompt 和模型回應都會被保存
