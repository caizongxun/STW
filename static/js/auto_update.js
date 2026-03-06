/**
 * 自動更新 JavaScript
 * 支持定時更新 AI 分析
 */

const autoUpdateState = {
    enabled: false,
    interval: null,
    updateFrequency: 900000, // 15 分鐘 (預設)
    lastUpdate: null
};

const autoUpdateElements = {
    toggleSwitch: document.getElementById('autoUpdateToggle'),
    frequency: document.getElementById('autoUpdateFrequency'),
    symbol: document.getElementById('autoUpdateSymbol'),
    timeframe: document.getElementById('autoUpdateTimeframe'),
    status: document.getElementById('autoUpdateStatus'),
    lastUpdateTime: document.getElementById('lastUpdateTime'),
    nextUpdateTime: document.getElementById('nextUpdateTime'),
    updateCount: document.getElementById('updateCount'),
    cardLoading: document.getElementById('autoUpdateCardLoading')
};

function initAutoUpdate() {
    setupAutoUpdateListeners();
    loadAutoUpdateConfig();
}

function setupAutoUpdateListeners() {
    autoUpdateElements.toggleSwitch.addEventListener('change', toggleAutoUpdate);
    autoUpdateElements.frequency.addEventListener('change', updateFrequency);
    autoUpdateElements.symbol.addEventListener('change', saveAutoUpdateConfig);
    autoUpdateElements.timeframe.addEventListener('change', saveAutoUpdateConfig);
}

async function loadAutoUpdateConfig() {
    try {
        const response = await fetch('/api/config/get');
        const config = await response.json();
        
        if (config.auto_update_symbol) {
            autoUpdateElements.symbol.value = config.auto_update_symbol;
        }
        
        if (config.auto_update_timeframe) {
            autoUpdateElements.timeframe.value = config.auto_update_timeframe;
        }
        
        if (config.auto_update_frequency) {
            autoUpdateElements.frequency.value = config.auto_update_frequency;
            autoUpdateState.updateFrequency = parseInt(config.auto_update_frequency);
        }
    } catch (error) {
        console.log('無法載入自動更新配置:', error);
    }
}

async function saveAutoUpdateConfig() {
    try {
        const config = {
            auto_update_symbol: autoUpdateElements.symbol.value,
            auto_update_timeframe: autoUpdateElements.timeframe.value,
            auto_update_frequency: autoUpdateElements.frequency.value
        };
        
        await fetch('/api/config/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        });
    } catch (error) {
        console.error('保存配置失敗:', error);
    }
}

function toggleAutoUpdate() {
    if (autoUpdateElements.toggleSwitch.checked) {
        startAutoUpdate();
    } else {
        stopAutoUpdate();
    }
}

function startAutoUpdate() {
    autoUpdateState.enabled = true;
    
    showAutoUpdateStatus('自動更新已啟動', 'success');
    
    // 立即執行一次
    performAutoUpdate();
    
    // 設置定時任務
    autoUpdateState.interval = setInterval(
        performAutoUpdate,
        autoUpdateState.updateFrequency
    );
    
    // 更新下次執行時間
    updateNextUpdateTime();
}

function stopAutoUpdate() {
    autoUpdateState.enabled = false;
    
    if (autoUpdateState.interval) {
        clearInterval(autoUpdateState.interval);
        autoUpdateState.interval = null;
    }
    
    showAutoUpdateStatus('自動更新已停止', 'info');
    autoUpdateElements.nextUpdateTime.textContent = 'N/A';
}

async function performAutoUpdate() {
    try {
        console.log('[Auto Update] 執行自動更新...');
        
        const symbol = autoUpdateElements.symbol.value;
        const timeframe = autoUpdateElements.timeframe.value;
        
        // 呼叫 AI 分析 API
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                symbol: symbol,
                timeframe: timeframe,
                auto_log: true  // 自動記錄到 AI 預測
            })
        });
        
        if (!response.ok) {
            throw new Error('分析失敗');
        }
        
        const data = await response.json();
        
        // 更新狀態
        autoUpdateState.lastUpdate = new Date();
        autoUpdateElements.lastUpdateTime.textContent = formatTime(autoUpdateState.lastUpdate);
        
        const currentCount = parseInt(autoUpdateElements.updateCount.textContent);
        autoUpdateElements.updateCount.textContent = currentCount + 1;
        
        showAutoUpdateStatus(
            `更新成功: ${data.decision.action} (信心度 ${data.decision.confidence}%)`,
            'success'
        );
        
        // 更新下次執行時間
        updateNextUpdateTime();
        
        console.log('[Auto Update] 更新完成');
        
    } catch (error) {
        console.error('[Auto Update] 錯誤:', error);
        showAutoUpdateStatus(`更新失敗: ${error.message}`, 'error');
    }
}

function updateFrequency() {
    const newFrequency = parseInt(autoUpdateElements.frequency.value);
    autoUpdateState.updateFrequency = newFrequency;
    
    saveAutoUpdateConfig();
    
    // 如果正在運行，重新啟動
    if (autoUpdateState.enabled) {
        stopAutoUpdate();
        autoUpdateElements.toggleSwitch.checked = true;
        startAutoUpdate();
    }
    
    const minutes = Math.floor(newFrequency / 60000);
    showAutoUpdateStatus(`更新頻率已調整為 ${minutes} 分鐘`, 'info');
}

function updateNextUpdateTime() {
    if (!autoUpdateState.lastUpdate) {
        autoUpdateElements.nextUpdateTime.textContent = '計算中...';
        return;
    }
    
    const nextUpdate = new Date(autoUpdateState.lastUpdate.getTime() + autoUpdateState.updateFrequency);
    autoUpdateElements.nextUpdateTime.textContent = formatTime(nextUpdate);
    
    // 每秒更新倒數計時
    if (autoUpdateState.countdownInterval) {
        clearInterval(autoUpdateState.countdownInterval);
    }
    
    autoUpdateState.countdownInterval = setInterval(() => {
        if (!autoUpdateState.enabled) {
            clearInterval(autoUpdateState.countdownInterval);
            return;
        }
        
        const now = new Date();
        const remaining = nextUpdate - now;
        
        if (remaining <= 0) {
            autoUpdateElements.nextUpdateTime.textContent = '即將執行...';
        } else {
            const minutes = Math.floor(remaining / 60000);
            const seconds = Math.floor((remaining % 60000) / 1000);
            autoUpdateElements.nextUpdateTime.textContent = 
                `${formatTime(nextUpdate)} (倒數 ${minutes}:${seconds.toString().padStart(2, '0')})`;
        }
    }, 1000);
}

function showAutoUpdateStatus(message, type) {
    let className = 'info-banner';
    if (type === 'error') className += ' error';
    
    autoUpdateElements.status.innerHTML = `
        <div class="${className}" style="margin: 16px 0;">
            <p>${message}</p>
        </div>
    `;
}

function formatTime(date) {
    return date.toLocaleString('zh-TW', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// WebSocket 事件
socket.on('auto_update_executed', (data) => {
    console.log('Auto update executed:', data);
    showAutoUpdateStatus(
        `AI 分析: ${data.action} (信心度 ${data.confidence}%)`,
        'success'
    );
});

document.addEventListener('DOMContentLoaded', initAutoUpdate);
