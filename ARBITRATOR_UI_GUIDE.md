# 🎯 兩階段仲裁 UI 顯示指南

## 🎉 功能介紹

系統現在支持**兩階段仲裁決策**，並在網頁中清晰顯示每個階段的結果：

### 階段 1: 兩個快速模型分析
```
┌─────────────────┬─────────────────┐
│   Model A       │   Model B       │
│ Llama 70B      │ Gemini 2.0     │
│ OPEN_LONG 85%  │ HOLD 65%       │
│ RSI超賣...    │ 成交量不足... │
└─────────────────┴─────────────────┘
         ↓
   ⚠️ 意見分歧 → 需要仲裁
```

### 階段 2: 仲裁者決策 (只在分歧時顯示)
```
┌──────────────────────────────────┐
│   🧠 Arbitrator           │
│   Llama 3.1 405B             │
│                                │
│   綜合兩個模型的分析，   │
│   雖然成交量略低，但技術 │
│   指標明確顯示超賣反彈， │
│   建議 OPEN_LONG (78%)      │
└──────────────────────────────────┘
```

### 最終決策
```
✅ OPEN_LONG (78%)
進場: $68,250
止損: $67,100 (-1.68%)
止盈: $71,500 (+4.76%)
風險收益比: 1:2.8
決策來源: 仲裁者
```

---

## 🛠️ 安裝步驟

### 1. 更新代碼

```bash
cd STW
git pull origin main
```

### 2. 修改 HTML 模板

編輯 `templates/index.html`，在 `</body>` 標籤之前添加：

```html
<!-- 兩階段仲裁 UI -->
<script src="{{ url_for('static', filename='js/arbitrator_ui.js') }}"></script>
```

### 3. 配置 config.json

```json
{
  "use_arbitrator_consensus": true,
  
  "GROQ_API_KEY": "gsk_...",
  "GOOGLE_API_KEY": "AIza_...",
  "OPENROUTER_API_KEY": "sk-or-v1_..."
}
```

### 4. 重啟系統

```bash
python app_flask.py
```

---

## 💻 修改 app_flask.py

在 `/api/analyze` 路由中添加支持：

```python
@app.route('/api/analyze', methods=['POST'])
def analyze_market():
    try:
        # ... 獲取市場數據 ...
        
        # 檢查是否使用兩階段仲裁
        use_arbitrator = config_data.get('use_arbitrator_consensus', False)
        
        if use_arbitrator:
            from core.arbitrator_consensus_agent import ArbitratorConsensusAgent
            
            agent = ArbitratorConsensusAgent()
            
            # 調用兩階段分析
            result = agent.analyze_with_arbitration(
                market_data=market_data,
                account_info=account_info,
                position_info=position_info
            )
            
            # 返回詳細結果
            return jsonify({
                'success': True,
                'mode': 'arbitrator',
                'stage_1': {
                    'model_a': {
                        'name': 'Llama 70B (Groq)',
                        'action': result.get('model_a_action'),
                        'confidence': result.get('model_a_confidence'),
                        'reasoning': result.get('model_a_reasoning'),
                        'elapsed': result.get('model_a_elapsed', 0)
                    },
                    'model_b': {
                        'name': 'Gemini 2.0 Flash',
                        'action': result.get('model_b_action'),
                        'confidence': result.get('model_b_confidence'),
                        'reasoning': result.get('model_b_reasoning'),
                        'elapsed': result.get('model_b_elapsed', 0)
                    },
                    'agreed': result.get('action') == result.get('model_a_action')
                },
                'stage_2': {
                    'needed': result.get('arbitration', False),
                    'arbitrator': {
                        'name': 'Llama 405B',
                        'reasoning': result.get('arbitrator_reasoning', ''),
                        'elapsed': result.get('arbitrator_elapsed', 0)
                    } if result.get('arbitration') else None
                },
                'final_decision': {
                    'action': result.get('action'),
                    'confidence': result.get('confidence'),
                    'reasoning': result.get('reasoning'),
                    'entry_price': result.get('entry_price'),
                    'stop_loss': result.get('stop_loss'),
                    'take_profit': result.get('take_profit'),
                    'risk_reward_ratio': result.get('risk_reward_ratio'),
                    'source': '仲裁者' if result.get('arbitration') else '兩模型共識'
                },
                'current_price': latest_price
            })
        
        # ... 原來的逻輯 ...
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## 📊 修改 main.js

在 `static/js/main.js` 中處理兩階段結果：

```javascript
function handleAnalyzeResponse(data) {
    if (data.mode === 'arbitrator') {
        // 顯示兩階段仲裁 UI
        window.arbitratorUI.show();
        window.arbitratorUI.reset();
        
        // 階段 1: 更新 Model A
        window.arbitratorUI.updateModelA(data.stage_1.model_a);
        
        // 階段 1: 更新 Model B
        window.arbitratorUI.updateModelB(data.stage_1.model_b);
        
        // 更新共識狀態
        window.arbitratorUI.updateConsensusStatus(
            data.stage_1.agreed,
            data.stage_1.model_a.action,
            data.stage_1.model_b.action
        );
        
        // 階段 2: 如果需要仲裁
        if (data.stage_2.needed && data.stage_2.arbitrator) {
            window.arbitratorUI.showArbitrator();
            window.arbitratorUI.updateArbitrator(data.stage_2.arbitrator);
        }
        
        // 最終決策
        window.arbitratorUI.updateFinalDecision(
            data.final_decision,
            data.final_decision.source
        );
    } else {
        // 隱藏兩階段 UI，顯示原來的結果
        if (window.arbitratorUI) {
            window.arbitratorUI.hide();
        }
        
        // ... 原來的處理逻輯 ...
    }
}
```

---

## 🎉 效果預覽

### 當兩個模型同意時

```
┌────────────────────────────────────────────────────┐
│            🧠 兩階段仲裁決策                        │
├────────────────────────────────────────────────────┤
│  階段 1  兩個快速模型分析                       │
├───────────────────────┬─────────────────────────┤
│ 🤖 Llama 70B      2.1s │ 🤖 Gemini 2.0    3.5s │
│ OPEN_LONG         85% │ OPEN_LONG        88% │
│ RSI(28)超賣，MACD金叉 │ 技術指標多頭排列    │
├───────────────────────┴─────────────────────────┤
│        ✅ 兩個模型同意: OPEN_LONG               │
├────────────────────────────────────────────────────┤
│              ✅ 最終決策                         │
│         OPEN_LONG (86%)                         │
│         進場: $68,250                            │
│         止損: $67,100 (-1.68%)                  │
│         止盈: $71,500 (+4.76%)                  │
│         決策來源: 兩模型共識                  │
└────────────────────────────────────────────────────┘
```

### 當兩個模型分歧時

```
┌────────────────────────────────────────────────────┐
│            🧠 兩階段仲裁決策                        │
├────────────────────────────────────────────────────┤
│  階段 1  兩個快速模型分析                       │
├───────────────────────┬─────────────────────────┤
│ 🤖 Llama 70B      2.1s │ 🤖 Gemini 2.0    3.5s │
│ OPEN_LONG         82% │ HOLD             65% │
│ RSI(28)超賣，MACD金叉 │ 成交量不足，建議觀望 │
├───────────────────────┴─────────────────────────┤
│     ⚠️ 意見分歧: OPEN_LONG vs HOLD → 需要仲裁   │
├────────────────────────────────────────────────────┤
│  階段 2  仲裁者最終決策                         │
├────────────────────────────────────────────────────┤
│  🧠 Llama 405B                           8.5s  │
│                                                  │
│  綜合兩個模型的分析，雖然成交量略低，        │
│  但技術指標明確顯示超賣反彈訊號，且          │
│  突破關鍵支撐位，建議 OPEN_LONG                │
├────────────────────────────────────────────────────┤
│              ✅ 最終決策                         │
│         OPEN_LONG (78%)                         │
│         進場: $68,250                            │
│         止損: $67,100 (-1.68%)                  │
│         止盈: $71,500 (+4.76%)                  │
│         決策來源: 🧠 仲裁者                    │
└────────────────────────────────────────────────────┘
```

---

## ✅ 優勢

1. **透明度高**
   - 看到每個模型的分析過程
   - 瞭解模型的推理遏輯

2. **可追蹤**
   - 知道決策來源 (共識 or 仲裁)
   - 方便後續優化和分析

3. **更好的決策**
   - 不會因分歧就放棄機會
   - 由最強模型仲裁

4. **學習價值**
   - 可以比較不同模型的分析
   - 學習哪些因素影響決策

---

**最後更新**: 2026 年 3 月 7 日
