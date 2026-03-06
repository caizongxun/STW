/**
 * Bybit Demo 交易 JavaScript
 */

const bybitState = {
    isConnected: false,
    isTrading: false,
    updateInterval: null
};

const bybitElements = {
    apiKey: document.getElementById('bybitApiKey'),
    apiSecret: document.getElementById('bybitApiSecret'),
    symbol: document.getElementById('bybitSymbol'),
    testBtn: document.getElementById('bybitTestBtn'),
    startBtn: document.getElementById('bybitStartBtn'),
    stopBtn: document.getElementById('bybitStopBtn'),
    accountInfo: document.getElementById('bybitAccountInfo'),
    totalEquity: document.getElementById('bybitTotalEquity'),
    available: document.getElementById('bybitAvailable'),
    pnl: document.getElementById('bybitPnl'),
    position: document.getElementById('bybitPosition'),
    status: document.getElementById('bybitStatus'),
    cardLoading: document.getElementById('bybitCardLoading')
};

function initBybit() {
    setupBybitEventListeners();
}

function setupBybitEventListeners() {
    bybitElements.testBtn.addEventListener('click', testBybitConnection);
    bybitElements.startBtn.addEventListener('click', startBybitTrading);
    bybitElements.stopBtn.addEventListener('click', stopBybitTrading);
}

async function testBybitConnection() {
    const apiKey = bybitElements.apiKey.value;
    const apiSecret = bybitElements.apiSecret.value;
    
    if (!apiKey || !apiSecret) {
        showBybitStatus('請先輸入 API Key 和 Secret', 'error');
        return;
    }
    
    showCardLoading('bybitCardLoading', '連線中...');
    
    try {
        const response = await fetch('/api/bybit/test', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                api_key: apiKey,
                api_secret: apiSecret,
                symbol: bybitElements.symbol.value
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            bybitState.isConnected = true;
            showBybitStatus(`連線成功! 餘額: $${data.balance.total_equity.toLocaleString()}`, 'success');
            updateBybitAccountInfo(data.balance, data.position);
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        showBybitStatus(`連線失敗: ${error.message}`, 'error');
    } finally {
        hideCardLoading('bybitCardLoading');
    }
}

async function startBybitTrading() {
    if (!bybitState.isConnected) {
        showBybitStatus('請先測試連線', 'error');
        return;
    }
    
    bybitState.isTrading = true;
    bybitElements.startBtn.disabled = true;
    bybitElements.stopBtn.disabled = false;
    
    showBybitStatus('自動交易已啟動', 'success');
    
    // 通知伺服器啟動交易
    socket.emit('start_bybit_trading', {
        api_key: bybitElements.apiKey.value,
        api_secret: bybitElements.apiSecret.value,
        symbol: bybitElements.symbol.value
    });
}

function stopBybitTrading() {
    bybitState.isTrading = false;
    bybitElements.startBtn.disabled = false;
    bybitElements.stopBtn.disabled = true;
    
    showBybitStatus('自動交易已停止', 'info');
    
    socket.emit('stop_bybit_trading');
}

function updateBybitAccountInfo(balance, position) {
    bybitElements.accountInfo.style.display = 'grid';
    
    bybitElements.totalEquity.textContent = `$${balance.total_equity.toLocaleString()}`;
    bybitElements.available.textContent = `$${balance.available_balance.toLocaleString()}`;
    bybitElements.pnl.textContent = `$${balance.unrealized_pnl.toLocaleString()}`;
    
    if (position) {
        bybitElements.position.textContent = `${position.side} ${position.size}`;
    } else {
        bybitElements.position.textContent = '無';
    }
}

function showBybitStatus(message, type) {
    let className = '';
    if (type === 'success') className = 'info-banner';
    else if (type === 'error') className = 'info-banner' + ' error';
    else className = 'info-banner';
    
    bybitElements.status.innerHTML = `
        <div class="${className}" style="margin: 0;">
            <p>${message}</p>
        </div>
    `;
}

// WebSocket 事件
socket.on('bybit_trade_executed', (data) => {
    console.log('Bybit trade executed:', data);
    updateBybitAccountInfo(data.balance, data.position);
    showBybitStatus(`交易執行: ${data.action} - ${data.message}`, 'success');
});

socket.on('bybit_account_updated', (data) => {
    console.log('Bybit account updated:', data);
    updateBybitAccountInfo(data.balance, data.position);
});

document.addEventListener('DOMContentLoaded', initBybit);
