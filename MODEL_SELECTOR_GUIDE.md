# 🤖 模型選擇器使用指南

## 功能簡介

讓你在 Web 界面自由選擇：
- **Model A**：快速模型（第一個分析者）
- **Model B**：快速模型（第二個分析者）
- **仲裁者**：決策模型（當 A 和 B 分歧時介入）

---

## 💻 在 Flask 中整合

### 1. 在 `app_flask.py` 中增加 API 路由

```python
from core.model_config_manager import ModelConfigManager

# 初始化
model_config_manager = ModelConfigManager()

# API: 獲取可用模型列表
@app.route('/api/models/available', methods=['GET'])
def get_available_models():
    try:
        models = model_config_manager.get_available_models()
        return jsonify({
            'success': True,
            'models': models
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 獲取當前配置
@app.route('/api/models/config', methods=['GET'])
def get_model_config():
    try:
        config = model_config_manager.get_config()
        summary = model_config_manager.get_config_summary()
        return jsonify({
            'success': True,
            'config': config,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 保存模型配置
@app.route('/api/models/config', methods=['POST'])
def save_model_config():
    try:
        config = request.json
        
        # 驗證配置
        is_valid, error_msg = model_config_manager.validate_config(config)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # 保存
        if model_config_manager.save_config(config):
            return jsonify({
                'success': True,
                'message': '配置已保存，請重新啟動佺服器以生效'
            })
        else:
            return jsonify({
                'success': False,
                'error': '保存失敗'
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 重置為預設
@app.route('/api/models/reset', methods=['POST'])
def reset_model_config():
    try:
        if model_config_manager.reset_to_default():
            return jsonify({
                'success': True,
                'message': '已重置為預設配置'
            })
        else:
            return jsonify({
                'success': False,
                'error': '重置失敗'
            }), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 2. 在 `templates/index.html` 中增加

```html
<!-- 在 <head> 中增加 CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/model_selector.css') }}">

<!-- 在頁面中增加容器 -->
<div id="model-selector-container"></div>

<!-- 在 </body> 前增加 JS -->
<script src="{{ url_for('static', filename='js/model_selector.js') }}"></script>
```

### 3. 修改 `arbitrator_consensus_agent.py` 讀取配置

```python
from core.model_config_manager import ModelConfigManager

class ArbitratorConsensusAgent:
    def __init__(self):
        # 讀取用戶選擇的模型配置
        self.model_config_manager = ModelConfigManager()
        self.user_config = self.model_config_manager.get_config()
        
        # 根據配置初始化模型
        self._init_models_from_config()
```

---

## 🎯 可選模型列表

### Groq 模型
| 模型 | 速度 | 額度 | 品質 | 適用 |
|------|------|------|------|------|
| Llama 3.3 70B | 1-3s | 14,400/天 | ⭐⭐⭐⭐⭐ | Model A/B |
| Mixtral 8x7B | 1-3s | 14,400/天 | ⭐⭐⭐⭐ | Model A/B |

### Google 模型
| 模型 | 速度 | 額度 | 品質 | 適用 |
|------|------|------|------|------|
| Gemini 2.0 Flash | 2-5s | 1,500/天 | ⭐⭐⭐⭐⭐ | Model A/B |
| Gemini 2.0 Flash Thinking | 5-10s | 500/天 | ⭐⭐⭐⭐⭐⭐ | 仲裁者 |

### OpenRouter 模型
| 模型 | 速度 | 額度 | 品質 | 適用 |
|------|------|------|------|------|
| DeepSeek R1 | 10-20s | 200/天 | ⭐⭐⭐⭐⭐ | 仲裁者 |
| Llama 3.3 70B | 5-10s | 200/天 | ⭐⭐⭐⭐ | Model A/B |

---

## 👁 界面預覽

```
┌─────────────────────────────────────────────────┐
│  🤖 模型選擇器                                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  🎯 Model A (快速模型)                         │
│  ┌────────────────────────────────────────┐  │
│  │ Groq - Llama 3.3 70B            ▼ │  │
│  └────────────────────────────────────────┘  │
│  [Groq] 速度: 1-3s | 額度: 14,400/day | ⭐⭐⭐⭐⭐ │
│                                                 │
│  🎯 Model B (快速模型)                         │
│  ┌────────────────────────────────────────┐  │
│  │ Google - Gemini 2.0 Flash      ▼ │  │
│  └────────────────────────────────────────┘  │
│  [Google] 速度: 2-5s | 額度: 1,500/day | ⭐⭐⭐⭐⭐ │
│                                                 │
│  🧠 仲裁者 (決策模型)                         │
│  ┌────────────────────────────────────────┐  │
│  │ Google - Gemini Thinking      ▼ │  │
│  └────────────────────────────────────────┘  │
│  [Google] 速度: 5-10s | 額度: 500/day | ⭐⭐⭐⭐⭐⭐ │
│                                                 │
│  [ 💾 保存配置 ]  [ 🔄 重置為預設 ]          │
│                                                 │
│  ✅ 配置已保存，重新啟動後生效                  │
└─────────────────────────────────────────────────┘
```

---

## 💡 使用流程

1. **打開 Web 界面**
   - 訪問 `http://localhost:5000`

2. **選擇模型**
   - Model A: 選擇一個快速模型（建議 Groq Llama 70B）
   - Model B: 選擇另一個快速模型（建議 Gemini Flash）
   - 仲裁者: 選擇推理模型（建議 Gemini Thinking）

3. **保存配置**
   - 點擊「💾 保存配置」
   - 系統會驗證配置是否有效

4. **重新啟動伺服器**
   ```bash
   python app_flask.py
   ```

5. **檢查配置**
   - 啟動時會顯示當前使用的模型

---

## 🔧 常見問題

### Q: 為什麼有些模型顯示「未配置 API Key」？
**A:** 需要先在「配置管理」中設定對應的 API Key。

### Q: Model A 和 Model B 可以選擇相同的模型嗎？
**A:** 不可以，系統會阻止你選擇相同的模型。

### Q: 保存後為什麼需要重新啟動？
**A:** 因為模型的初始化是在伺服器啟動時進行的，修改配置後需要重新讀取。

### Q: 推薦的配置組合是什麼？
**A:** 方案 B（預設）
- Model A: Groq Llama 70B
- Model B: Google Gemini Flash
- 仲裁者: Google Gemini Thinking

這個組合速度快、穩定性高、額度大。

---

## 🚀 下一步

1. **自動備用機制**
   - 當選擇的模型失敗時，自動切換到備用模型

2. **效能監控**
   - 在 UI 顯示每個模型的響應時間和成功率

3. **動態調整**
   - 根據模型表現自動調整優先級

4. **A/B 測試**
   - 同時運行多個配置，比較效果
