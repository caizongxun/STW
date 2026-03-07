/**
 * 主 JavaScript 邏輯
 * 修復: 優先顯示 adjusted_confidence
 */

const socket = io();

const state = {
    currentTab: 'signal',
    isAnalyzing: false,
    isBacktesting: false,
    latestSignal: null
};

const elements = {
    navItems: document.querySelectorAll('.nav-item'),
    tabContents: document.querySelectorAll('.tab-content'),
    wsStatus: document.getElementById('wsStatus'),
    wsStatusText: document.getElementById('wsStatusText'),
    currentTime: document.getElementById('currentTime'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText: document.getElementById('loadingText'),
    
    symbolSelect: document.getElementById('symbolSelect'),
    timeframeSelect: document.getElementById('timeframeSelect'),
    capitalInput: document.getElementById('capitalInput'),
    daysInput: document.getElementById('daysInput'),
    confidenceSlider: document.getElementById('confidenceSlider'),
    confidenceValue: document.getElementById('confidenceValue'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    backtestBtn: document.getElementById('backtestBtn'),
    signalContent: document.getElementById('signalContent'),
    backtestResults: document.getElementById('backtestResults'),
    backtestContent: document.getElementById('backtestContent')
};

function init() {
    setupEventListeners();
    setupWebSocket();
    updateTime();
    setInterval(updateTime, 1000);
}

function setupEventListeners() {
    elements.navItems.forEach(item => {
        item.addEventListener('click', () => {
            switchTab(item.dataset.tab);
        });
    });
    
    elements.confidenceSlider.addEventListener('input', (e) => {
        elements.confidenceValue.textContent = e.target.value + '%';
    });
    
    elements.analyzeBtn.addEventListener('click', analyzeMarket);
    elements.backtestBtn.addEventListener('click', runBacktest);
}

function setupWebSocket() {
    socket.on('connect', () => {
        console.log('WebSocket connected');
        updateConnectionStatus(true);
    });
    
    socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);
    });
    
    socket.on('signal_updated', (data) => {
        console.log('Signal updated:', data);
        state.latestSignal = data;
        displaySignal(data);
    });
}

function switchTab(tabName) {
    state.currentTab = tabName;
    
    elements.navItems.forEach(item => {
        if (item.dataset.tab === tabName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    elements.tabContents.forEach(content => {
        if (content.id === `${tabName}-tab`) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

function updateConnectionStatus(isConnected) {
    if (isConnected) {
        elements.wsStatus.classList.add('connected');
        elements.wsStatusText.textContent = '已連接';
    } else {
        elements.wsStatus.classList.remove('connected');
        elements.wsStatusText.textContent = '斷線';
    }
}

function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
    elements.currentTime.textContent = timeString;
}

// 模塊級 loading
function showCardLoading(cardId, text = '處理中...') {
    const loading = document.getElementById(cardId);
    if (loading) {
        loading.querySelector('.card-loading-text').textContent = text;
        loading.classList.add('active');
    }
}

function hideCardLoading(cardId) {
    const loading = document.getElementById(cardId);
    if (loading) {
        loading.classList.remove('active');
    }
}

function showLoading(message = '處理中...') {
    elements.loadingText.textContent = message;
    elements.loadingOverlay.classList.add('active');
}

function hideLoading() {
    elements.loadingOverlay.classList.remove('active');
}

function showError(message) {
    alert('錯誤: ' + message);
}

function showSuccess(message) {
    console.log('成功:', message);
}

async function analyzeMarket() {
    if (state.isAnalyzing) return;
    
    state.isAnalyzing = true;
    elements.analyzeBtn.disabled = true;
    showCardLoading('resultCardLoading', 'AI 分析中...');
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                symbol: elements.symbolSelect.value,
                timeframe: elements.timeframeSelect.value
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '分析失敗');
        }
        
        state.latestSignal = data;
        displaySignal(data);
        showSuccess('AI 分析完成');
        
        // 觸發 AI 分析完成事件 (用於更新懸浮球聊天室)
        window.dispatchEvent(new CustomEvent('aiAnalysisComplete'));
        
    } catch (error) {
        showError(error.message);
    } finally {
        state.isAnalyzing = false;
        elements.analyzeBtn.disabled = false;
        hideCardLoading('resultCardLoading');
    }
}

function displaySignal(data) {
    const decision = data.decision;
    const action = decision.final_action || decision.action || 'HOLD';
    
    // 修復: 優先使用 adjusted_confidence，其次是 confidence
    const confidence = decision.adjusted_confidence !== undefined ? 
                       decision.adjusted_confidence : 
                       (decision.confidence || 0);
    
    // 獲取 action 的顯示信息
    const actionInfo = getActionInfo(action);
    
    let html = `
        <div class="signal-result">
            <div class="signal-header" style="background: ${actionInfo.bgColor}; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: ${actionInfo.textColor}; margin: 0 0 10px 0;">${actionInfo.text}</h2>
                <p style="color: ${actionInfo.textColor}; margin: 0; font-size: 18px;">信心度: ${confidence}%</p>
            </div>
            
            <div class="stats-grid" style="margin-bottom: 20px;">
                <div class="stat-card">
                    <div class="stat-label">幣種</div>
                    <div class="stat-value" style="font-size: 18px;">${data.symbol}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">周期</div>
                    <div class="stat-value" style="font-size: 18px;">${data.timeframe}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">當前價格</div>
                    <div class="stat-value" style="font-size: 18px;">$${parseFloat(data.price).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">時間</div>
                    <div class="stat-value" style="font-size: 14px;">${new Date(data.timestamp).toLocaleString('zh-TW', {year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'})}</div>
                </div>
            </div>
    `;
    
    // 如果有三階段仲裁資訊
    if (decision.execution_decision) {
        html += `
            <div class="stats-grid" style="margin-bottom: 20px;">
                <div class="stat-card">
                    <div class="stat-label">執行決策</div>
                    <div class="stat-value" style="font-size: 16px; color: ${decision.execution_decision === 'EXECUTE' ? 'var(--success-color)' : 'var(--warning-color)'}">
                        ${decision.execution_decision}
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">模型類型</div>
                    <div class="stat-value" style="font-size: 16px;">${decision.model_type || 'single'}</div>
                </div>
                ${decision.agreement !== undefined ? `
                <div class="stat-card">
                    <div class="stat-label">模型A/B共識</div>
                    <div class="stat-value" style="font-size: 16px;">${decision.agreement ? '✅ 一致' : '❌ 分歧'}</div>
                </div>
                ` : ''}
                ${decision.is_counter_trend !== undefined ? `
                <div class="stat-card">
                    <div class="stat-label">逆勢操作</div>
                    <div class="stat-value" style="font-size: 16px;">${decision.is_counter_trend ? '✅ 是' : '❌ 否'}</div>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    // 如果有止損止盈資訊
    if (decision.stop_loss && decision.take_profit) {
        html += `
            <div class="stats-grid" style="margin-bottom: 20px;">
                <div class="stat-card">
                    <div class="stat-label">止損</div>
                    <div class="stat-value" style="font-size: 18px; color: var(--danger-color);">$${parseFloat(decision.stop_loss).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">止盈</div>
                    <div class="stat-value" style="font-size: 18px; color: var(--success-color);">$${parseFloat(decision.take_profit).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">倉位</div>
                    <div class="stat-value" style="font-size: 18px;">${decision.adjusted_position_size || decision.position_size_usdt || 0} USDT</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">槓桿</div>
                    <div class="stat-value" style="font-size: 18px;">${decision.adjusted_leverage || decision.leverage || 1}x</div>
                </div>
            </div>
        `;
    }
    
    // AI 推理
    const reasoning = decision.executor_reasoning || decision.reasoning || '';
    if (reasoning) {
        html += `
            <div style="background: var(--bg-dark); padding: 16px; border-radius: 8px; border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 12px 0; color: var(--primary-color);">AI 推理</h4>
                <p style="margin: 0; color: var(--text-secondary); line-height: 1.6; white-space: pre-wrap;">${reasoning.substring(0, 800)}${reasoning.length > 800 ? '...' : ''}</p>
            </div>
        `;
    }
    
    html += '</div>';
    
    elements.signalContent.innerHTML = html;
}

function getActionInfo(action) {
    const actionMap = {
        'OPEN_LONG': {
            text: '看多訊號',
            bgColor: 'rgba(0, 255, 136, 0.15)',
            textColor: 'var(--success-color)'
        },
        'OPEN_SHORT': {
            text: '看空訊號',
            bgColor: 'rgba(255, 68, 68, 0.15)',
            textColor: 'var(--danger-color)'
        },
        'ADD_POSITION': {
            text: '加倉訊號',
            bgColor: 'rgba(0, 212, 255, 0.15)',
            textColor: 'var(--primary-color)'
        },
        'CLOSE': {
            text: '平倉訊號',
            bgColor: 'rgba(255, 170, 0, 0.15)',
            textColor: 'var(--warning-color)'
        },
        'HOLD': {
            text: '觀望',
            bgColor: 'rgba(139, 146, 168, 0.15)',
            textColor: 'var(--text-secondary)'
        }
    };
    
    return actionMap[action] || actionMap['HOLD'];
}

async function runBacktest() {
    if (state.isBacktesting) return;
    
    state.isBacktesting = true;
    elements.backtestBtn.disabled = true;
    showCardLoading('backtestCardLoading', '回測中...');
    elements.backtestResults.style.display = 'block';
    
    try {
        const response = await fetch('/api/backtest', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                symbol: elements.symbolSelect.value,
                timeframe: elements.timeframeSelect.value,
                capital: parseFloat(elements.capitalInput.value),
                simulation_days: parseInt(elements.daysInput.value),
                ai_confidence_threshold: parseFloat(elements.confidenceSlider.value) / 100
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '回測失敗');
        }
        
        displayBacktestResults(data);
        showSuccess('回測完成');
        
    } catch (error) {
        showError(error.message);
    } finally {
        state.isBacktesting = false;
        elements.backtestBtn.disabled = false;
        hideCardLoading('backtestCardLoading');
    }
}

function displayBacktestResults(results) {
    let html = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">總報酬</div>
                <div class="stat-value" style="color: ${results.return_pct >= 0 ? 'var(--success-color)' : 'var(--danger-color)'}">
                    ${results.return_pct.toFixed(2)}%
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-label">勝率</div>
                <div class="stat-value">${results.win_rate.toFixed(1)}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">總交易</div>
                <div class="stat-value">${results.total_trades}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">最大回撤</div>
                <div class="stat-value" style="color: var(--danger-color)">
                    ${results.max_drawdown.toFixed(2)}%
                </div>
            </div>
        </div>
        
        <div class="stats-grid" style="margin-top: 16px;">
            <div class="stat-card">
                <div class="stat-label">Sharpe Ratio</div>
                <div class="stat-value">${results.sharpe_ratio ? results.sharpe_ratio.toFixed(2) : 'N/A'}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">盈虧比</div>
                <div class="stat-value">${results.profit_factor ? results.profit_factor.toFixed(2) : 'N/A'}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">平均持倉</div>
                <div class="stat-value">${results.avg_holding_hours ? results.avg_holding_hours.toFixed(1) + 'h' : 'N/A'}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">月報酬</div>
                <div class="stat-value">${results.monthly_return ? results.monthly_return.toFixed(2) + '%' : 'N/A'}</div>
            </div>
        </div>
    `;
    
    elements.backtestContent.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', init);
