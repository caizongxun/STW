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
    
    // API 設定
    deepseekApiKey: document.getElementById('deepseekApiKey'),
    binanceApiKey: document.getElementById('binanceApiKey'),
    
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
    
    // 狀態
    status: document.getElementById('configStatus'),
    cardLoading: document.getElementById('configCardLoading')
};

function initConfig() {
    setupConfigListeners();
    loadConfig();
}

function setupConfigListeners() {
    // 保存按鈕
    configElements.saveBtn.addEventListener('click', saveConfig);
    configElements.resetBtn.addEventListener('click', resetConfig);
    configElements.exportBtn.addEventListener('click', exportConfig);
    configElements.importBtn.addEventListener('click', importConfig);
    
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
        if (config.ai_temperature) configElements.aiTemperature.value = config.ai_temperature;
        if (config.ai_max_tokens) configElements.aiMaxTokens.value = config.ai_max_tokens;
        if (config.ai_confidence_threshold) configElements.aiConfidenceThreshold.value = config.ai_confidence_threshold;
        
        // API 設定 (只顯示提示)
        if (config.deepseek_api_key_saved) {
            configElements.deepseekApiKey.placeholder = '•••••••• (已保存)';
        }
        if (config.binance_api_key_saved) {
            configElements.binanceApiKey.placeholder = '•••••••• (已保存)';
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

async function saveConfig() {
    try {
        showCardLoading('configCardLoading', '保存中...');
        
        const config = {
            // AI 設定
            ai_model: configElements.aiModel.value,
            ai_temperature: parseFloat(configElements.aiTemperature.value),
            ai_max_tokens: parseInt(configElements.aiMaxTokens.value),
            ai_confidence_threshold: parseFloat(configElements.aiConfidenceThreshold.value),
            
            // 通知設定
            enable_notifications: configElements.enableNotifications.checked,
            notification_email: configElements.notificationEmail.value,
            notify_on_trade: configElements.notifyOnTrade.checked,
            notify_on_error: configElements.notifyOnError.checked
        };
        
        // API 金鑰 (只有輸入時才保存)
        if (configElements.deepseekApiKey.value) {
            config.deepseek_api_key = configElements.deepseekApiKey.value;
        }
        if (configElements.binanceApiKey.value) {
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
            <p>${message}</p>
        </div>
    `;
    
    setTimeout(() => {
        configElements.status.innerHTML = '';
    }, 3000);
}

document.addEventListener('DOMContentLoaded', initConfig);
