/**
 * 主 JavaScript 邏輯
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

// 全局 loading (只用於極特殊情況)
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
    const action = decision.action || 'HOLD';
    const confidence = decision.confidence || 0;
    
    let html = `
        <div class="signal-card">
            <div class="signal-header ${action.toLowerCase()}">
                <h4>${getActionText(action)}</h4>
                <span class="confidence">信心度: ${confidence}%</span>
            </div>
            
            <div class="signal-metrics">
                <div class="metric">
                    <label>幣種</label>
                    <value>${data.symbol} (${data.timeframe})</value>
                </div>
                <div class="metric">
                    <label>當前價格</label>
                    <value>$${data.price.toLocaleString()}</value>
                </div>
                <div class="metric">
                    <label>時間</label>
                    <value>${new Date(data.timestamp).toLocaleString('zh-TW')}</value>
                </div>
            </div>
            
            ${decision.stop_loss ? `
            <div class="signal-details">
                <div class="detail-item">
                    <span>止損:</span>
                    <span>$${decision.stop_loss.toLocaleString()}</span>
                </div>
                <div class="detail-item">
                    <span>止盈:</span>
                    <span>$${decision.take_profit.toLocaleString()}</span>
                </div>
                <div class="detail-item">
                    <span>倉位:</span>
                    <span>${decision.position_size_usdt} USDT</span>
                </div>
                <div class="detail-item">
                    <span>桶桿:</span>
                    <span>${decision.leverage}x</span>
                </div>
            </div>
            ` : ''}
            
            ${decision.reasoning ? `
            <div class="signal-reasoning">
                <h5>AI 推理</h5>
                <p>${decision.reasoning.substring(0, 300)}...</p>
            </div>
            ` : ''}
        </div>
    `;
    
    elements.signalContent.innerHTML = html;
}

function getActionText(action) {
    const actionMap = {
        'OPEN_LONG': '看多訊號',
        'OPEN_SHORT': '看空訊號',
        'ADD_POSITION': '加倉',
        'CLOSE': '平倉',
        'HOLD': '觀望'
    };
    return actionMap[action] || action;
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
    `;
    
    elements.backtestContent.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', init);
