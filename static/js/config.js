/**
 * 系統設定 JavaScript
 * 管理 AI 模型、API 金鑰、通知等設定
 */

const configState = {
    config: {},
    isDirty: false
};

const configElements = {
    // AI 設定
    aiModel: document.getElementById('aiModel'),
    aiTemperature: document.getElementById('aiTemperature'),
    aiMaxTokens: document.getElementById('aiMaxTokens'),
    aiConfidenceThreshold: document.getElementById('aiConfidenceThreshold'),
    
    // 兩階段仲裁
    useArbitratorConsensus: document.getElementById('useArbitratorConsensus'),
    
    // 多 API 設定
    groqApiKey: document.getElementById('groqApiKey'),
    googleApiKey: document.getElementById('googleApiKey'),
    openrouterApiKey: document.getElementById('openrouterApiKey'),
    githubToken: document.getElementById('githubToken'),
    cloudflareAccountId: document.getElementById('cloudflareAccountId'),
    cloudflareApiKey: document.getElementById('cloudflareApiKey'),
    
    // 舊 API
    deepseekApiKey: document.getElementById('deepseekApiKey'),
    binanceApiKey: document.getElementById('binanceApiKey'),
    
    // 集成設定
    enableEnsemble: document.getElementById('enableEnsemble'),
    minModels: document.getElementById('minModels'),
    maxModels: document.getElementById('maxModels'),
    
    // 通知設定
    enableNotifications: document.getElementById('enableNotifications'),
    notificationEmail: document.getElementById('notificationEmail'),
    notifyOnTrade: document.getElementById('notifyOnTrade'),
    notifyOnError: document.getElementById('notifyOnError'),
    
    // 按鈕
    saveBtn: document.getElementById('saveConfigBtn'),
    resetBtn: document.getElementById('resetConfigBtn'),
    exportBtn: document.getElementById('exportConfigBtn'),
    importBtn: document.getElementById('importConfigBtn'),
    testApisBtn: document.getElementById('testApisBtn'),
    
    // 狀態
    status: document.getElementById('configStatus'),
    cardLoading: document.getElementById('configCardLoading'),
    apiStats: document.getElementById('apiStats')
};

function initConfig() {
    setupConfigListeners();
    loadConfig();
    loadApiStats();
}

function setupConfigListeners() {
    // 保存按鈕
    configElements.saveBtn.addEventListener('click', saveConfig);
    configElements.resetBtn.addEventListener('click', resetConfig);
    configElements.exportBtn.addEventListener('click', exportConfig);
    configElements.importBtn.addEventListener('click', importConfig);
    
    if (configElements.testApisBtn) {
        configElements.testApisBtn.addEventListener('click', testApis);
    }
    
    // 追蹤變更
    Object.keys(configElements).forEach(key => {
        const element = configElements[key];
        if (element && (element.tagName === 'INPUT' || element.tagName === 'SELECT')) {
            element.addEventListener('change', () => {
                configState.isDirty = true;
                updateSaveButton();
            });
        }
    });
}

async function loadConfig() {
    try {
        showCardLoading('configCardLoading', '載入設定...');
        
        const response = await fetch('/api/config/get');
        const config = await response.json();
        
        configState.config = config;
        
        // AI 設定
        if (config.ai_model) configElements.aiModel.value = config.ai_model;
        if (config.ai_temperature !== undefined) configElements.aiTemperature.value = config.ai_temperature;
        if (config.ai_max_tokens) configElements.aiMaxTokens.value = config.ai_max_tokens;
        if (config.ai_confidence_threshold !== undefined) configElements.aiConfidenceThreshold.value = config.ai_confidence_threshold;
        
        // 兩階段仲裁
        if (configElements.useArbitratorConsensus && config.use_arbitrator_consensus !== undefined) {
            configElements.useArbitratorConsensus.checked = config.use_arbitrator_consensus;
        }
        
        // 多 API 設定 (顯示掩碼)
        setApiKeyField('groqApiKey', config.groq_api_key_saved);
        setApiKeyField('googleApiKey', config.google_api_key_saved);
        setApiKeyField('openrouterApiKey', config.openrouter_api_key_saved);
        setApiKeyField('githubToken', config.github_token_saved);
        setApiKeyField('cloudflareApiKey', config.cloudflare_api_key_saved);
        
        // Cloudflare Account ID (顯示实际值，不需掉码)
        if (config.cloudflare_account_id && configElements.cloudflareAccountId) {
            configElements.cloudflareAccountId.value = config.cloudflare_account_id;
        }
        
        // 舊 API
        setApiKeyField('deepseekApiKey', config.deepseek_api_key_saved);
        setApiKeyField('binanceApiKey', config.binance_api_key_saved);
        
        // 集成設定
        if (config.enable_ensemble !== undefined && configElements.enableEnsemble) {
            configElements.enableEnsemble.checked = config.enable_ensemble;
        }
        if (config.min_models && configElements.minModels) {
            configElements.minModels.value = config.min_models;
        }
        if (config.max_models && configElements.maxModels) {
            configElements.maxModels.value = config.max_models;
        }
        
        // 通知設定
        if (config.enable_notifications !== undefined) {
            configElements.enableNotifications.checked = config.enable_notifications;
        }
        if (config.notification_email) {
            configElements.notificationEmail.value = config.notification_email;
        }
        if (config.notify_on_trade !== undefined) {
            configElements.notifyOnTrade.checked = config.notify_on_trade;
        }
        if (config.notify_on_error !== undefined) {
            configElements.notifyOnError.checked = config.notify_on_error;
        }
        
        configState.isDirty = false;
        updateSaveButton();
        
        showConfigStatus('設定已載入', 'success');
        
    } catch (error) {
        console.error('載入設定失敗:', error);
        showConfigStatus('載入失敗', 'error');
    } finally {
        hideCardLoading('configCardLoading');
    }
}

function setApiKeyField(elementId, isSaved) {
    const element = configElements[elementId];
    if (!element) return;
    
    if (isSaved) {
        element.placeholder = '•••••••• (已保存)';
        element.value = '';
    } else {
        element.placeholder = '輸入 API Key';
    }
}

async function saveConfig() {
    try {
        showCardLoading('configCardLoading', '保存中...');
        
        const config = {
            // AI 設定
            ai_model: configElements.aiModel.value,
            ai_temperature: parseFloat(configElements.aiTemperature.value),
            ai_max_tokens: parseInt(configElements.aiMaxTokens.value),
            ai_confidence_threshold: parseFloat(configElements.aiConfidenceThreshold.value),
            
            // 兩階段仲裁
            use_arbitrator_consensus: configElements.useArbitratorConsensus ? configElements.useArbitratorConsensus.checked : false,
            
            // 集成設定
            enable_ensemble: configElements.enableEnsemble ? configElements.enableEnsemble.checked : false,
            min_models: configElements.minModels ? parseInt(configElements.minModels.value) : 2,
            max_models: configElements.maxModels ? parseInt(configElements.maxModels.value) : 3,
            
            // 通知設定
            enable_notifications: configElements.enableNotifications.checked,
            notification_email: configElements.notificationEmail.value,
            notify_on_trade: configElements.notifyOnTrade.checked,
            notify_on_error: configElements.notifyOnError.checked
        };
        
        // API 金鑰 (只有輸入時才保存)
        if (configElements.groqApiKey && configElements.groqApiKey.value) {
            config.groq_api_key = configElements.groqApiKey.value;
        }
        if (configElements.googleApiKey && configElements.googleApiKey.value) {
            config.google_api_key = configElements.googleApiKey.value;
        }
        if (configElements.openrouterApiKey && configElements.openrouterApiKey.value) {
            config.openrouter_api_key = configElements.openrouterApiKey.value;
        }
        if (configElements.githubToken && configElements.githubToken.value) {
            config.github_token = configElements.githubToken.value;
        }
        
        // Cloudflare Account ID + API Key
        if (configElements.cloudflareAccountId && configElements.cloudflareAccountId.value) {
            config.cloudflare_account_id = configElements.cloudflareAccountId.value;
        }
        if (configElements.cloudflareApiKey && configElements.cloudflareApiKey.value) {
            config.cloudflare_api_key = configElements.cloudflareApiKey.value;
        }
        
        if (configElements.deepseekApiKey && configElements.deepseekApiKey.value) {
            config.deepseek_api_key = configElements.deepseekApiKey.value;
        }
        if (configElements.binanceApiKey && configElements.binanceApiKey.value) {
            config.binance_api_key = configElements.binanceApiKey.value;
        }
        
        const response = await fetch('/api/config/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        });
        
        if (response.ok) {
            configState.isDirty = false;
            updateSaveButton();
            showConfigStatus('設定已保存', 'success');
            
            // 清空密碼框
            if (configElements.groqApiKey) configElements.groqApiKey.value = '';
            if (configElements.googleApiKey) configElements.googleApiKey.value = '';
            if (configElements.openrouterApiKey) configElements.openrouterApiKey.value = '';
            if (configElements.githubToken) configElements.githubToken.value = '';
            if (configElements.cloudflareApiKey) configElements.cloudflareApiKey.value = '';
            if (configElements.deepseekApiKey) configElements.deepseekApiKey.value = '';
            if (configElements.binanceApiKey) configElements.binanceApiKey.value = '';
            
            // 重新載入配置
            await loadConfig();
            await loadApiStats();
        } else {
            throw new Error('保存失敗');
        }
        
    } catch (error) {
        console.error('保存設定失敗:', error);
        showConfigStatus('保存失敗', 'error');
    } finally {
        hideCardLoading('configCardLoading');
    }
}

async function loadApiStats() {
    if (!configElements.apiStats) return;
    
    try {
        const response = await fetch('/api/config/api-stats');
        const stats = await response.json();
        
        if (stats.total_providers === 0) {
            configElements.apiStats.innerHTML = `
                <div class="info-banner" style="margin: 16px 0;">
                    <p>尚未配置任何 API Key</p>
                </div>
            `;
            return;
        }
        
        let html = '<div class="stats-grid" style="margin: 16px 0;">';
        
        html += `
            <div class="stat-card">
                <div class="stat-label">總 API 數</div>
                <div class="stat-value">${stats.total_providers}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">可用 API</div>
                <div class="stat-value">${stats.available_providers}</div>
            </div>
        `;
        
        html += '</div>';
        
        // 各 API 詳情
        html += '<div class="table-container" style="margin: 16px 0;">';
        html += '<table><thead><tr>';
        html += '<th>API 提供商</th><th>模型</th><th>每日使用</th><th>優先級</th><th>狀態</th>';
        html += '</tr></thead><tbody>';
        
        stats.providers.forEach(provider => {
            const statusBadge = provider.is_available 
                ? '<span class="badge badge-success">正常</span>' 
                : '<span class="badge badge-error">不可用</span>';
            
            html += `
                <tr>
                    <td>${provider.name}</td>
                    <td>${provider.model}</td>
                    <td>${provider.daily_usage}</td>
                    <td>${provider.priority}</td>
                    <td>${statusBadge}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        
        configElements.apiStats.innerHTML = html;
        
    } catch (error) {
        console.error('載入 API 統計失敗:', error);
    }
}

async function testApis() {
    try {
        showCardLoading('configCardLoading', '測試中...');
        
        const response = await fetch('/api/config/test-apis', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        let message = `測試完成\n可用: ${result.available}/${result.total}`;
        
        if (result.failed.length > 0) {
            message += `\n失敗: ${result.failed.join(', ')}`;
        }
        
        showConfigStatus(message, result.available > 0 ? 'success' : 'error');
        await loadApiStats();
        
    } catch (error) {
        console.error('測試 API 失敗:', error);
        showConfigStatus('測試失敗', 'error');
    } finally {
        hideCardLoading('configCardLoading');
    }
}

async function resetConfig() {
    if (!confirm('確定要重設所有設定嗎？')) {
        return;
    }
    
    try {
        const response = await fetch('/api/config/reset', {
            method: 'POST'
        });
        
        if (response.ok) {
            await loadConfig();
            await loadApiStats();
            showConfigStatus('設定已重設', 'success');
        }
    } catch (error) {
        console.error('重設失敗:', error);
        showConfigStatus('重設失敗', 'error');
    }
}

function exportConfig() {
    const dataStr = JSON.stringify(configState.config, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `stw-config-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    showConfigStatus('設定已匯出', 'success');
}

function importConfig() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        try {
            const text = await file.text();
            const config = JSON.parse(text);
            
            const response = await fetch('/api/config/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });
            
            if (response.ok) {
                await loadConfig();
                await loadApiStats();
                showConfigStatus('設定已匯入', 'success');
            }
        } catch (error) {
            console.error('匯入失敗:', error);
            showConfigStatus('匯入失敗', 'error');
        }
    };
    
    input.click();
}

function updateSaveButton() {
    if (configState.isDirty) {
        configElements.saveBtn.textContent = '保存變更 *';
        configElements.saveBtn.classList.add('btn-warning');
    } else {
        configElements.saveBtn.textContent = '保存設定';
        configElements.saveBtn.classList.remove('btn-warning');
    }
}

function showConfigStatus(message, type) {
    let className = 'info-banner';
    if (type === 'error') className += ' error';
    
    configElements.status.innerHTML = `
        <div class="${className}" style="margin: 16px 0;">
            <p>${message.replace(/\n/g, '<br>')}</p>
        </div>
    `;
    
    setTimeout(() => {
        configElements.status.innerHTML = '';
    }, 5000);
}

document.addEventListener('DOMContentLoaded', initConfig);
