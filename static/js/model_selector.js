/**
 * 模型選擇器 UI
 * 讓用戶在 Web 界面選擇 Model A, Model B, 仲裁者
 * 支持熱更新（不用重啟）
 */

class ModelSelector {
    constructor() {
        this.availableModels = [];
        this.currentConfig = {
            model_a: null,
            model_b: null,
            arbitrator: null
        };
        this.init();
    }

    async init() {
        await this.loadAvailableModels();
        await this.loadCurrentConfig();
        this.renderUI();
        this.attachEventListeners();
    }

    async loadAvailableModels() {
        try {
            const response = await fetch('/api/models/available');
            const data = await response.json();
            if (data.success) {
                this.availableModels = data.models;
            }
        } catch (error) {
            console.error('讀取可用模型失敗:', error);
        }
    }

    async loadCurrentConfig() {
        try {
            const response = await fetch('/api/models/config');
            const data = await response.json();
            if (data.success) {
                this.currentConfig = data.config;
            }
        } catch (error) {
            console.error('讀取模型配置失敗:', error);
        }
    }

    renderUI() {
        const container = document.getElementById('model-selector-container');
        if (!container) return;

        container.innerHTML = `
            <div class="model-selector-panel">
                <div class="model-selector-header">
                    <h3>🤖 模型選擇器</h3>
                    <span class="model-selector-badge">熱更新</span>
                </div>
                
                <!-- Model A -->
                <div class="model-select-group">
                    <label for="model-a-select">
                        <span class="model-label">Model A (所有模型)</span>
                        <span class="model-hint">可選擇任何模型，包含大型模型</span>
                    </label>
                    <select id="model-a-select" class="model-select">
                        <option value="">請選擇...</option>
                        ${this.renderModelOptions('all')}
                    </select>
                    <div class="model-info" id="model-a-info"></div>
                </div>

                <!-- Model B -->
                <div class="model-select-group">
                    <label for="model-b-select">
                        <span class="model-label">Model B (所有模型)</span>
                        <span class="model-hint">可選擇任何模型，包含大型模型</span>
                    </label>
                    <select id="model-b-select" class="model-select">
                        <option value="">請選擇...</option>
                        ${this.renderModelOptions('all')}
                    </select>
                    <div class="model-info" id="model-b-info"></div>
                </div>

                <!-- 仲裁者 -->
                <div class="model-select-group">
                    <label for="arbitrator-select">
                        <span class="model-label">仲裁者 (所有模型)</span>
                        <span class="model-hint">建議選擇大型模型 (Llama 405B, GPT-4o, DeepSeek R1)</span>
                    </label>
                    <select id="arbitrator-select" class="model-select">
                        <option value="">請選擇...</option>
                        ${this.renderModelOptions('all')}
                    </select>
                    <div class="model-info" id="arbitrator-info"></div>
                </div>

                <!-- 按鈕 -->
                <div class="model-select-actions">
                    <button id="save-model-config" class="btn btn-primary">
                        💾 保存配置（熱更新）
                    </button>
                    <button id="reset-model-config" class="btn btn-secondary">
                        🔄 重置為預設
                    </button>
                </div>

                <!-- 狀態顯示 -->
                <div id="model-status" class="model-status"></div>
            </div>
        `;

        // 設定當前值
        this.setCurrentValues();
    }

    renderModelOptions(filter = 'all') {
        // 按平台分組，排序
        const grouped = {};
        this.availableModels.forEach(model => {
            if (!grouped[model.platform]) {
                grouped[model.platform] = [];
            }
            grouped[model.platform].push(model);
        });

        // 按平台排序：Groq > GitHub > Cloudflare > OpenRouter > Google
        const platformOrder = ['Groq', 'GitHub Models', 'Cloudflare', 'OpenRouter', 'Google'];
        
        let html = '';
        platformOrder.forEach(platform => {
            if (grouped[platform]) {
                html += `<optgroup label="${platform}">`;
                grouped[platform].forEach(model => {
                    const disabled = !model.available ? 'disabled' : '';
                    const label = model.available ? '' : ' (未配置 API Key)';
                    html += `<option value="${model.id}" ${disabled}>
                        ${model.name} [${model.quota}] ${label}
                    </option>`;
                });
                html += '</optgroup>';
            }
        });

        return html;
    }

    setCurrentValues() {
        if (this.currentConfig.model_a) {
            document.getElementById('model-a-select').value = this.currentConfig.model_a;
            this.updateModelInfo('model-a', this.currentConfig.model_a);
        }
        if (this.currentConfig.model_b) {
            document.getElementById('model-b-select').value = this.currentConfig.model_b;
            this.updateModelInfo('model-b', this.currentConfig.model_b);
        }
        if (this.currentConfig.arbitrator) {
            document.getElementById('arbitrator-select').value = this.currentConfig.arbitrator;
            this.updateModelInfo('arbitrator', this.currentConfig.arbitrator);
        }
    }

    attachEventListeners() {
        // Model A 選擇
        document.getElementById('model-a-select').addEventListener('change', (e) => {
            this.updateModelInfo('model-a', e.target.value);
        });

        // Model B 選擇
        document.getElementById('model-b-select').addEventListener('change', (e) => {
            this.updateModelInfo('model-b', e.target.value);
        });

        // 仲裁者選擇
        document.getElementById('arbitrator-select').addEventListener('change', (e) => {
            this.updateModelInfo('arbitrator', e.target.value);
        });

        // 保存按鈕
        document.getElementById('save-model-config').addEventListener('click', () => {
            this.saveConfig();
        });

        // 重置按鈕
        document.getElementById('reset-model-config').addEventListener('click', () => {
            this.resetToDefault();
        });
    }

    updateModelInfo(target, modelId) {
        if (!modelId) return;

        const model = this.availableModels.find(m => m.id === modelId);
        if (!model) return;

        const infoDiv = document.getElementById(`${target}-info`);
        const stars = '⭐'.repeat(model.quality);
        
        // 根據速度顯示顏色
        let speedClass = 'speed-fast';
        if (model.speed.includes('10-20s')) speedClass = 'speed-slow';
        else if (model.speed.includes('5-10s')) speedClass = 'speed-medium';
        
        infoDiv.innerHTML = `
            <div class="model-details">
                <span class="badge badge-${model.platform.toLowerCase().replace(' ', '-')}">${model.platform}</span>
                <span class="model-speed ${speedClass}">⏱️ ${model.speed}</span>
                <span class="model-quota">📊 ${model.quota}</span>
                <span class="model-quality">${stars} (${model.quality}/6)</span>
                <span class="model-recommend">🎯 ${model.recommended_for}</span>
            </div>
        `;
    }

    async saveConfig() {
        const modelA = document.getElementById('model-a-select').value;
        const modelB = document.getElementById('model-b-select').value;
        const arbitrator = document.getElementById('arbitrator-select').value;

        if (!modelA || !modelB || !arbitrator) {
            this.showStatus('請選擇所有模型', 'warning');
            return;
        }

        // 顯示 loading
        const saveBtn = document.getElementById('save-model-config');
        const originalText = saveBtn.textContent;
        saveBtn.disabled = true;
        saveBtn.textContent = '🔄 保存中...';

        try {
            const response = await fetch('/api/models/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model_a: modelA,
                    model_b: modelB,
                    arbitrator: arbitrator
                })
            });

            const data = await response.json();
            if (data.success) {
                // 試著熱更新
                this.showStatus('✅ 配置已保存，正在熱更新...', 'success');
                
                this.currentConfig = {
                    model_a: modelA,
                    model_b: modelB,
                    arbitrator: arbitrator
                };
                
                // 呼叫熱更新 API
                try {
                    const hotReloadResponse = await fetch('/api/models/hot-reload', {
                        method: 'POST'
                    });
                    const hotReloadData = await hotReloadResponse.json();
                    
                    if (hotReloadData.success) {
                        this.showStatus('✅ 配置已保存並立即生效！', 'success');
                    } else {
                        this.showStatus('⚠️ 配置已保存，但熱更新失敗，請重啟應用', 'warning');
                    }
                } catch (hotReloadError) {
                    console.error('熱更新失敗:', hotReloadError);
                    this.showStatus('⚠️ 配置已保存，但熱更新失敗，請重啟應用', 'warning');
                }
            } else {
                this.showStatus('❌ 保存失敗: ' + data.error, 'error');
            }
        } catch (error) {
            this.showStatus('❌ 保存失敗: ' + error.message, 'error');
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = originalText;
        }
    }

    async resetToDefault() {
        if (!confirm('確定要重置為預設配置嗎？')) return;

        try {
            const response = await fetch('/api/models/reset', {
                method: 'POST'
            });

            const data = await response.json();
            if (data.success) {
                this.showStatus('✅ 已重置為預設配置並立即生效', 'success');
                await this.loadCurrentConfig();
                this.setCurrentValues();
            }
        } catch (error) {
            this.showStatus('重置失敗: ' + error.message, 'error');
        }
    }

    showStatus(message, type = 'info') {
        const statusDiv = document.getElementById('model-status');
        statusDiv.className = `model-status status-${type}`;
        statusDiv.textContent = message;
        
        // 成功消息 3 秒後清除，其他 5 秒
        const timeout = type === 'success' ? 3000 : 5000;
        setTimeout(() => {
            statusDiv.textContent = '';
            statusDiv.className = 'model-status';
        }, timeout);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('model-selector-container')) {
        new ModelSelector();
    }
});
