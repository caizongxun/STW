/**
 * 模型選擇器 UI
 * 讓用戶在 Web 界面選擇 Model A, Model B, 仲裁者
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
                <h3>模型選擇器</h3>
                
                <!-- Model A -->
                <div class="model-select-group">
                    <label for="model-a-select">
                        <span class="model-label">Model A (快速模型)</span>
                    </label>
                    <select id="model-a-select" class="model-select">
                        <option value="">請選擇...</option>
                        ${this.renderModelOptions('fast')}
                    </select>
                    <div class="model-info" id="model-a-info"></div>
                </div>

                <!-- Model B -->
                <div class="model-select-group">
                    <label for="model-b-select">
                        <span class="model-label">Model B (快速模型)</span>
                    </label>
                    <select id="model-b-select" class="model-select">
                        <option value="">請選擇...</option>
                        ${this.renderModelOptions('fast')}
                    </select>
                    <div class="model-info" id="model-b-info"></div>
                </div>

                <!-- 仲裁者 -->
                <div class="model-select-group">
                    <label for="arbitrator-select">
                        <span class="model-label">仲裁者 (決策模型)</span>
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
                        保存配置
                    </button>
                    <button id="reset-model-config" class="btn btn-secondary">
                        重置為預設
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
        return this.availableModels
            .filter(model => {
                if (filter === 'fast') return model.category === 'fast';
                return true;
            })
            .map(model => {
                const disabled = !model.available ? 'disabled' : '';
                const label = model.available ? '' : ' (未配置 API Key)';
                return `<option value="${model.id}" ${disabled}>
                    ${model.platform} - ${model.name} ${label}
                </option>`;
            })
            .join('');
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
        infoDiv.innerHTML = `
            <div class="model-details">
                <span class="badge badge-${model.platform.toLowerCase()}">${model.platform}</span>
                <span class="model-speed">速度: ${model.speed}</span>
                <span class="model-quota">額度: ${model.quota}</span>
                <span class="model-quality">品質: ${stars}</span>
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
                this.showStatus('配置已保存，重新啟動後生效', 'success');
                this.currentConfig = {
                    model_a: modelA,
                    model_b: modelB,
                    arbitrator: arbitrator
                };
            } else {
                this.showStatus('保存失敗: ' + data.error, 'error');
            }
        } catch (error) {
            this.showStatus('保存失敗: ' + error.message, 'error');
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
                this.showStatus('已重置為預設配置', 'success');
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
        
        setTimeout(() => {
            statusDiv.textContent = '';
            statusDiv.className = 'model-status';
        }, 5000);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('model-selector-container')) {
        new ModelSelector();
    }
});
