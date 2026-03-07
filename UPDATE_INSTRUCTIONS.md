# 更新說明 - Prompt 和模型回應顯示

## 已完成修正

### 1. 修正 `core/arbitrator_consensus_agent.py`

✅ **修正 Prompt 加入歷史 K 棒和成功案例**
- `_prepare_prompts()` 現在會包含 `historical_candles` (前 20 根 K 棒)
- 加入 `successful_cases` (最多 10 個成功案例)
- 加入 `recent_decisions` (最近 5 次決策)

✅ **記錄詳細分析過程**
- 新增 `self.last_analysis_detail` 字典記錄：
  - `system_prompt`: 系統 prompt
  - `user_prompt`: 使用者 prompt
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

## 需要手動完成的步驟

### 3. 更新 `app_flask.py`

請在 `app_flask.py` 中加入以下程式碼：

#### Step 3.1: 在檔案開頭的 import 區塊加入：

```python
# 導入分析詳細 API 路由
try:
    from api_routes_analysis_detail import register_analysis_detail_routes
    HAS_ANALYSIS_DETAIL = True
except ImportError as e:
    HAS_ANALYSIS_DETAIL = False
    print(f"警告: 分析詳細功能不可用 - {e}")
```

#### Step 3.2: 在 `if __name__ == '__main__':` 區塊中，在 `load_cases()` 之後加入：

```python
if __name__ == '__main__':
    load_config()
    load_cases()
    
    # 註冊模型選擇器 API 路由
    if HAS_MODEL_SELECTOR:
        register_model_selector_routes(app, app_state)
        print("✅ 模型選擇器功能已啟用 (支持熱更新)")
    
    # 註冊分析詳細 API 路由
    if HAS_ANALYSIS_DETAIL:
        register_analysis_detail_routes(app, app_state)
        print("✅ 分析詳細功能已啟用")
    
    print("")
    # ... 其他啟動程式碼
```

---

### 4. 前端顯示功能

需要在前端 (HTML/JavaScript) 加入顯示功能：

#### 建議加入以下功能：

1. **實時預測 Tab 中加入「查看 Prompt 詳細」按鈕**
   - 點擊後顯示 Modal 視窗
   - 顯示 System Prompt
   - 顯示 User Prompt (包含歷史 K 棒、成功案例)
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
                    <div class="modal-content">
                        <h3>Prompt 詳細資訊</h3>
                        <p><strong>時間:</strong> ${detail.timestamp}</p>
                        
                        <h4>System Prompt</h4>
                        <pre>${detail.prompts.system_prompt}</pre>
                        
                        <h4>User Prompt</h4>
                        <pre>${detail.prompts.user_prompt}</pre>
                        
                        <h4>Model A 回應</h4>
                        <p><strong>模型:</strong> ${detail.model_responses.model_a.model_name}</p>
                        <p><strong>決策:</strong> ${detail.model_responses.model_a.action}</p>
                        <p><strong>信心度:</strong> ${detail.model_responses.model_a.confidence}%</p>
                        <pre>${detail.model_responses.model_a.full_response}</pre>
                        
                        <h4>Model B 回應</h4>
                        <p><strong>模型:</strong> ${detail.model_responses.model_b.model_name}</p>
                        <p><strong>決策:</strong> ${detail.model_responses.model_b.action}</p>
                        <p><strong>信心度:</strong> ${detail.model_responses.model_b.confidence}%</p>
                        <pre>${detail.model_responses.model_b.full_response}</pre>
                        
                        ${detail.model_responses.arbitrator ? `
                            <h4>仲裁者回應</h4>
                            <p><strong>模型:</strong> ${detail.model_responses.arbitrator.model_name}</p>
                            <p><strong>決策:</strong> ${detail.model_responses.arbitrator.action}</p>
                            <p><strong>信心度:</strong> ${detail.model_responses.arbitrator.confidence}%</p>
                            <pre>${detail.model_responses.arbitrator.full_response}</pre>
                        ` : ''}
                        
                        <button onclick="this.parentElement.parentElement.remove()">Close</button>
                    </div>
                `;
                document.body.appendChild(modal);
            }
        });
}
```

---

## 使用方式

1. 啟動系統：`python app_flask.py`
2. 在實時預測介面點擊「分析市場」
3. 分析完成後，點擊「查看 Prompt 詳細」按鈕
4. 即可看到：
   - 完整的 System Prompt
   - 完整的 User Prompt (包含 20 根 K 棒 + 成功案例)
   - Model A 的完整回應
   - Model B 的完整回應
   - 仲裁者的完整回應 (如果有的話)

---

## 檔案更新清單

- [x] `core/arbitrator_consensus_agent.py` - 修正 prompt 加入歷史資料
- [x] `api_routes_analysis_detail.py` - 新增 API 路由
- [ ] `app_flask.py` - 註冊新 API
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
