/**
 * AI 預測記錄 JavaScript
 * 處理 AI 預測記錄的更新、顯示、導出
 */

const aiLogState = {
    logs: [],
    autoUpdateInterval: null
};

const aiLogElements = {
    symbol: document.getElementById('aiLogSymbol'),
    timeframe: document.getElementById('aiLogTimeframe'),
    autoUpdate: document.getElementById('aiLogAutoUpdate'),
    updateBtn: document.getElementById('aiLogUpdateBtn'),
    clearBtn: document.getElementById('aiLogClearBtn'),
    exportBtn: document.getElementById('aiLogExportBtn'),
    totalPredictions: document.getElementById('totalPredictions'),
    verifiedPredictions: document.getElementById('verifiedPredictions'),
    accuracy: document.getElementById('accuracy'),
    mostCommonAction: document.getElementById('mostCommonAction'),
    logsTableBody: document.getElementById('logsTableBody')
};

// ============= 初始化 =============

function initAILog() {
    setupAILogEventListeners();
    setupAILogWebSocket();
    loadAILogs();
}

function setupAILogEventListeners() {
    aiLogElements.updateBtn.addEventListener('click', updateAILog);
    aiLogElements.clearBtn.addEventListener('click', clearAILogs);
    aiLogElements.exportBtn.addEventListener('click', exportAILogs);
    
    aiLogElements.autoUpdate.addEventListener('change', (e) => {
        if (e.target.checked) {
            startAutoUpdate();
        } else {
            stopAutoUpdate();
        }
    });
}

function setupAILogWebSocket() {
    socket.on('ai_log_updated', (data) => {
        console.log('AI log updated:', data);
        aiLogState.logs = data.logs;
        renderAILogs();
        updateAILogStats();
    });
    
    socket.on('ai_log_cleared', () => {
        console.log('AI logs cleared');
        aiLogState.logs = [];
        renderAILogs();
        updateAILogStats();
    });
}

// ============= API 請求 =============

async function loadAILogs() {
    try {
        const response = await fetch('/api/ai-log/get');
        const data = await response.json();
        
        if (response.ok) {
            aiLogState.logs = data.logs || [];
            renderAILogs();
            updateAILogStats();
        }
    } catch (error) {
        console.error('Failed to load AI logs:', error);
    }
}

async function updateAILog() {
    aiLogElements.updateBtn.disabled = true;
    showLoading('🤖 獲取 AI 預測...');
    
    try {
        const response = await fetch('/api/ai-log/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: aiLogElements.symbol.value,
                timeframe: aiLogElements.timeframe.value
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '更新失敗');
        }
        
        aiLogState.logs = data.logs || [];
        renderAILogs();
        updateAILogStats();
        showSuccess('更新成功');
        
    } catch (error) {
        showError(error.message);
    } finally {
        aiLogElements.updateBtn.disabled = false;
        hideLoading();
    }
}

async function clearAILogs() {
    if (!confirm('確定要清除所有記錄嗎？')) {
        return;
    }
    
    try {
        const response = await fetch('/api/ai-log/clear', {
            method: 'POST'
        });
        
        if (response.ok) {
            aiLogState.logs = [];
            renderAILogs();
            updateAILogStats();
            showSuccess('記錄已清除');
        }
    } catch (error) {
        showError(error.message);
    }
}

function exportAILogs() {
    if (aiLogState.logs.length === 0) {
        showError('無記錄可導出');
        return;
    }
    
    // 轉換為 CSV
    const headers = ['timestamp', 'symbol', 'timeframe', 'close_price', 'action', 'confidence', 
                     'predicted_direction', 'actual_direction', 'is_correct'];
    
    let csv = headers.join(',') + '\n';
    
    aiLogState.logs.forEach(log => {
        const row = headers.map(header => {
            const value = log[header];
            if (value === null || value === undefined) return '';
            if (typeof value === 'string' && value.includes(',')) {
                return `"${value}"`;
            }
            return value;
        });
        csv += row.join(',') + '\n';
    });
    
    // 下載
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `ai_predictions_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showSuccess('CSV 已下載');
}

// ============= 自動更新 =============

function startAutoUpdate() {
    if (aiLogState.autoUpdateInterval) {
        return;
    }
    
    updateAILog(); // 立即更新一次
    
    aiLogState.autoUpdateInterval = setInterval(() => {
        updateAILog();
    }, 5000); // 每 5 秒更新
    
    console.log('Auto update started');
}

function stopAutoUpdate() {
    if (aiLogState.autoUpdateInterval) {
        clearInterval(aiLogState.autoUpdateInterval);
        aiLogState.autoUpdateInterval = null;
        console.log('Auto update stopped');
    }
}

// ============= UI 更新 =============

function renderAILogs() {
    if (aiLogState.logs.length === 0) {
        aiLogElements.logsTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted">尚無記錄</td>
            </tr>
        `;
        return;
    }
    
    const rows = aiLogState.logs.slice().reverse().map(log => {
        const isCorrectIcon = log.is_correct === true ? '✅' : 
                             log.is_correct === false ? '❌' : '⏳';
        
        return `
            <tr>
                <td>${log.timestamp}</td>
                <td>$${log.close_price.toLocaleString()}</td>
                <td><span class="badge ${getActionBadgeClass(log.action)}">${log.action}</span></td>
                <td>${log.confidence}%</td>
                <td>${log.predicted_direction}</td>
                <td>${log.actual_direction || '-'}</td>
                <td class="text-center">${isCorrectIcon}</td>
            </tr>
        `;
    }).join('');
    
    aiLogElements.logsTableBody.innerHTML = rows;
}

function updateAILogStats() {
    const logs = aiLogState.logs;
    
    // 總預測次數
    aiLogElements.totalPredictions.textContent = logs.length;
    
    // 已驗證次數
    const verified = logs.filter(log => log.is_correct !== null).length;
    aiLogElements.verifiedPredictions.textContent = verified;
    
    // 準確率
    const correct = logs.filter(log => log.is_correct === true).length;
    const accuracy = verified > 0 ? (correct / verified * 100).toFixed(1) : 0;
    aiLogElements.accuracy.textContent = accuracy + '%';
    
    // 最常動作
    if (logs.length > 0) {
        const actionCounts = {};
        logs.forEach(log => {
            actionCounts[log.action] = (actionCounts[log.action] || 0) + 1;
        });
        
        const mostCommon = Object.entries(actionCounts)
            .sort((a, b) => b[1] - a[1])[0];
        
        aiLogElements.mostCommonAction.textContent = mostCommon ? mostCommon[0] : 'N/A';
    } else {
        aiLogElements.mostCommonAction.textContent = 'N/A';
    }
}

function getActionBadgeClass(action) {
    const classMap = {
        'OPEN_LONG': 'badge-success',
        'OPEN_SHORT': 'badge-danger',
        'ADD_POSITION': 'badge-info',
        'CLOSE': 'badge-warning',
        'HOLD': 'badge-secondary'
    };
    return classMap[action] || 'badge-secondary';
}

// ============= 啟動 =============

document.addEventListener('DOMContentLoaded', initAILog);
