/**
 * 學習案例庫 JavaScript
 * 管理成功交易案例，供 AI 學習
 */

const casesState = {
    cases: [],
    filteredCases: [],
    currentFilter: 'all',
    minProfitThreshold: 2.0,
    editingCase: null
};

const casesElements = {
    casesList: document.getElementById('casesList'),
    filterAll: document.getElementById('filterAll'),
    filterLong: document.getElementById('filterLong'),
    filterShort: document.getElementById('filterShort'),
    addCaseBtn: document.getElementById('addCaseBtn'),
    searchInput: document.getElementById('casesSearch'),
    totalCases: document.getElementById('totalCases'),
    avgProfit: document.getElementById('avgProfit'),
    winRate: document.getElementById('winRate'),
    cardLoading: document.getElementById('casesCardLoading')
};

function initCases() {
    setupCasesListeners();
    loadCases();
    loadCaseConfig();
}

function setupCasesListeners() {
    casesElements.filterAll.addEventListener('click', () => filterCases('all'));
    casesElements.filterLong.addEventListener('click', () => filterCases('long'));
    casesElements.filterShort.addEventListener('click', () => filterCases('short'));
    casesElements.addCaseBtn.addEventListener('click', showAddCaseModal);
    casesElements.searchInput.addEventListener('input', searchCases);
}

async function loadCaseConfig() {
    try {
        const response = await fetch('/api/config/get');
        const config = await response.json();
        
        if (config.min_profit_threshold) {
            casesState.minProfitThreshold = config.min_profit_threshold;
        }
    } catch (error) {
        console.log('無法載入案例配置:', error);
    }
}

async function loadCases() {
    try {
        showCardLoading('casesCardLoading', '載入中...');
        
        const response = await fetch('/api/cases/list');
        const data = await response.json();
        
        casesState.cases = data.cases || [];
        casesState.filteredCases = casesState.cases;
        
        updateCasesStats();
        renderCasesList();
        
    } catch (error) {
        console.error('載入案例失敗:', error);
        casesElements.casesList.innerHTML = `
            <div class="info-banner error">
                <p>載入失敗: ${error.message}</p>
            </div>
        `;
    } finally {
        hideCardLoading('casesCardLoading');
    }
}

function filterCases(filter) {
    casesState.currentFilter = filter;
    
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (filter === 'all') {
        casesElements.filterAll.classList.add('active');
        casesState.filteredCases = casesState.cases;
    } else if (filter === 'long') {
        casesElements.filterLong.classList.add('active');
        casesState.filteredCases = casesState.cases.filter(c => c.direction === 'LONG');
    } else if (filter === 'short') {
        casesElements.filterShort.classList.add('active');
        casesState.filteredCases = casesState.cases.filter(c => c.direction === 'SHORT');
    }
    
    renderCasesList();
}

function searchCases() {
    const query = casesElements.searchInput.value.toLowerCase();
    
    if (!query) {
        filterCases(casesState.currentFilter);
        return;
    }
    
    casesState.filteredCases = casesState.cases.filter(c => 
        c.symbol.toLowerCase().includes(query) ||
        c.reason.toLowerCase().includes(query) ||
        c.tags.some(tag => tag.toLowerCase().includes(query))
    );
    
    renderCasesList();
}

function renderCasesList() {
    if (casesState.filteredCases.length === 0) {
        casesElements.casesList.innerHTML = `
            <div class="info-banner">
                <p>無符合的案例</p>
            </div>
        `;
        return;
    }
    
    casesElements.casesList.innerHTML = casesState.filteredCases.map(caseItem => {
        const isQualified = caseItem.profit >= casesState.minProfitThreshold;
        const qualifiedBadge = isQualified ? 
            '<span class="badge success" style="background: #10b981;">✓ 合格</span>' : 
            '<span class="badge" style="background: #f59e0b;">⚠ 不合格</span>';
        
        return `
        <div class="case-card" data-id="${caseItem.id}" style="border-left: 4px solid ${isQualified ? '#10b981' : '#f59e0b'};">
            <div class="case-header">
                <div class="case-title">
                    <span class="badge ${caseItem.direction.toLowerCase()}">${caseItem.direction}</span>
                    ${qualifiedBadge}
                    <strong>${caseItem.symbol}</strong>
                    <span class="text-muted">${caseItem.timeframe}</span>
                </div>
                <div class="case-profit ${caseItem.profit > 0 ? 'positive' : 'negative'}">
                    ${caseItem.profit > 0 ? '+' : ''}${caseItem.profit.toFixed(2)}%
                </div>
            </div>
            
            <div class="case-body">
                <div class="case-info">
                    <div><strong>入場:</strong> $${caseItem.entry_price.toLocaleString()}</div>
                    <div><strong>出場:</strong> $${caseItem.exit_price.toLocaleString()}</div>
                    <div><strong>持倉:</strong> ${caseItem.holding_hours || 0}h</div>
                    <div><strong>槓桿:</strong> ${caseItem.leverage}x</div>
                </div>
                
                <div class="case-reason">
                    <strong>入場理由:</strong> ${caseItem.reason}
                </div>
                
                ${caseItem.exit_reason ? `
                <div class="case-reason" style="margin-top: 8px;">
                    <strong>出場理由:</strong> ${caseItem.exit_reason}
                </div>
                ` : ''}
                
                <div class="case-indicators">
                    <small>
                        RSI: ${caseItem.rsi.toFixed(2)} | 
                        MACD: ${caseItem.macd_hist.toFixed(4)} | 
                        ADX: ${caseItem.adx.toFixed(2)} |
                        BB: ${(caseItem.bb_position * 100).toFixed(1)}%
                    </small>
                </div>
                
                <div class="case-tags">
                    ${caseItem.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
                
                <div class="case-timestamp">
                    <small>入場: ${new Date(caseItem.entry_time).toLocaleString('zh-TW')}</small>
                </div>
            </div>
            
            <div class="case-actions">
                <button class="btn-sm btn-secondary" onclick="viewCase('${caseItem.id}')">檢視</button>
                <button class="btn-sm btn-danger" onclick="deleteCase('${caseItem.id}')">刪除</button>
            </div>
        </div>
    `}).join('');
}

function updateCasesStats() {
    const total = casesState.cases.length;
    casesElements.totalCases.textContent = total;
    
    if (total === 0) {
        casesElements.avgProfit.textContent = '0%';
        casesElements.winRate.textContent = '0%';
        return;
    }
    
    const qualifiedCases = casesState.cases.filter(c => c.profit >= casesState.minProfitThreshold);
    
    if (qualifiedCases.length > 0) {
        const avgProfit = qualifiedCases.reduce((sum, c) => sum + c.profit, 0) / qualifiedCases.length;
        casesElements.avgProfit.textContent = `${avgProfit > 0 ? '+' : ''}${avgProfit.toFixed(2)}%`;
    } else {
        casesElements.avgProfit.textContent = '0%';
    }
    
    const wins = casesState.cases.filter(c => c.profit > 0).length;
    const winRate = (wins / total) * 100;
    casesElements.winRate.textContent = `${winRate.toFixed(1)}%`;
}

function showAddCaseModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 800px; max-height: 90vh; overflow-y: auto;">
            <div class="modal-header">
                <h3>添加成功交易案例</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            
            <div class="modal-body">
                <div class="info-banner" style="margin-bottom: 20px;">
                    <p>記錄一個成功的交易，讓 AI 從中學習。只有盈利 ≥ ${casesState.minProfitThreshold}% 的案例才算合格。</p>
                </div>
                
                <h4>基本資訊</h4>
                <div class="grid-2" style="margin-bottom: 20px;">
                    <div class="form-group">
                        <label>交易對 *</label>
                        <select id="caseSymbol" class="form-control">
                            <option value="BTCUSDT">BTCUSDT</option>
                            <option value="ETHUSDT">ETHUSDT</option>
                            <option value="SOLUSDT">SOLUSDT</option>
                            <option value="BNBUSDT">BNBUSDT</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>K 線周期 *</label>
                        <select id="caseTimeframe" class="form-control">
                            <option value="15m">15m</option>
                            <option value="1h">1h</option>
                            <option value="4h">4h</option>
                            <option value="1d">1d</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>方向 *</label>
                        <select id="caseDirection" class="form-control">
                            <option value="LONG">做多 (LONG)</option>
                            <option value="SHORT">做空 (SHORT)</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>槓桿 *</label>
                        <input type="number" id="caseLeverage" class="form-control" value="1" min="1" max="10">
                    </div>
                </div>
                
                <h4>交易詳情</h4>
                <div class="grid-2" style="margin-bottom: 20px;">
                    <div class="form-group">
                        <label>入場價格 (USDT) *</label>
                        <input type="number" id="caseEntryPrice" class="form-control" step="0.01" required>
                    </div>
                    
                    <div class="form-group">
                        <label>出場價格 (USDT) *</label>
                        <input type="number" id="caseExitPrice" class="form-control" step="0.01" required>
                    </div>
                    
                    <div class="form-group">
                        <label>持倉時間 (小時)</label>
                        <input type="number" id="caseHoldingHours" class="form-control" value="1" min="0.25" step="0.25">
                    </div>
                    
                    <div class="form-group">
                        <label>盈虧 (%) *</label>
                        <input type="number" id="caseProfit" class="form-control" step="0.01" required>
                    </div>
                </div>
                
                <h4>技術指標 (入場時)</h4>
                <div class="grid-3" style="margin-bottom: 20px;">
                    <div class="form-group">
                        <label>RSI *</label>
                        <input type="number" id="caseRsi" class="form-control" value="50" min="0" max="100" step="0.1">
                    </div>
                    
                    <div class="form-group">
                        <label>MACD Histogram *</label>
                        <input type="number" id="caseMacdHist" class="form-control" value="0" step="0.0001">
                    </div>
                    
                    <div class="form-group">
                        <label>ADX *</label>
                        <input type="number" id="caseAdx" class="form-control" value="25" min="0" max="100" step="0.1">
                    </div>
                    
                    <div class="form-group">
                        <label>BB Position (0-1) *</label>
                        <input type="number" id="caseBbPosition" class="form-control" value="0.5" min="0" max="1" step="0.01">
                    </div>
                    
                    <div class="form-group">
                        <label>ATR</label>
                        <input type="number" id="caseAtr" class="form-control" value="0" step="0.01">
                    </div>
                    
                    <div class="form-group">
                        <label>Volume Ratio</label>
                        <input type="number" id="caseVolumeRatio" class="form-control" value="1" step="0.1">
                    </div>
                </div>
                
                <h4>理由與標籤</h4>
                <div class="form-group" style="margin-bottom: 15px;">
                    <label>入場理由 *</label>
                    <textarea id="caseReason" class="form-control" rows="3" 
                        placeholder="例如：RSI 超賣 + MACD 金叉 + 布林帶下軌支撐"
                        required></textarea>
                </div>
                
                <div class="form-group" style="margin-bottom: 15px;">
                    <label>出場理由</label>
                    <textarea id="caseExitReason" class="form-control" rows="2" 
                        placeholder="例如：觸及目標價 / RSI 過熟 / 趋勢反轉訊號"></textarea>
                </div>
                
                <div class="form-group" style="margin-bottom: 15px;">
                    <label>標籤 (逗號分隔)</label>
                    <input type="text" id="caseTags" class="form-control" 
                        placeholder="例如：超賣反彈,金叉,支撐位">
                </div>
                
                <div class="form-group">
                    <label>入場時間</label>
                    <input type="datetime-local" id="caseEntryTime" class="form-control">
                </div>
            </div>
            
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">取消</button>
                <button class="btn btn-primary" onclick="submitCase()">保存案例</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const now = new Date();
    document.getElementById('caseEntryTime').value = now.toISOString().slice(0, 16);
}

function closeModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        modal.remove();
    }
}

async function submitCase() {
    try {
        const direction = document.getElementById('caseDirection').value;
        const entryPrice = parseFloat(document.getElementById('caseEntryPrice').value);
        const exitPrice = parseFloat(document.getElementById('caseExitPrice').value);
        const profit = parseFloat(document.getElementById('caseProfit').value);
        
        if (!entryPrice || !exitPrice || isNaN(profit)) {
            alert('請填寫所有必填欄位');
            return;
        }
        
        const tags = document.getElementById('caseTags').value
            .split(',')
            .map(t => t.trim())
            .filter(t => t.length > 0);
        
        const caseData = {
            symbol: document.getElementById('caseSymbol').value,
            timeframe: document.getElementById('caseTimeframe').value,
            direction: direction,
            leverage: parseInt(document.getElementById('caseLeverage').value),
            entry_price: entryPrice,
            exit_price: exitPrice,
            holding_hours: parseFloat(document.getElementById('caseHoldingHours').value),
            profit: profit,
            rsi: parseFloat(document.getElementById('caseRsi').value),
            macd_hist: parseFloat(document.getElementById('caseMacdHist').value),
            adx: parseFloat(document.getElementById('caseAdx').value),
            bb_position: parseFloat(document.getElementById('caseBbPosition').value),
            atr: parseFloat(document.getElementById('caseAtr').value) || 0,
            volume_ratio: parseFloat(document.getElementById('caseVolumeRatio').value) || 1,
            reason: document.getElementById('caseReason').value,
            exit_reason: document.getElementById('caseExitReason').value || '',
            tags: tags,
            entry_time: document.getElementById('caseEntryTime').value
        };
        
        const response = await fetch('/api/cases/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(caseData)
        });
        
        if (response.ok) {
            closeModal();
            await loadCases();
            alert('案例已添加！');
        } else {
            const error = await response.json();
            alert(`添加失敗: ${error.error}`);
        }
        
    } catch (error) {
        console.error('添加案例失敗:', error);
        alert('添加失敗');
    }
}

async function deleteCase(id) {
    if (!confirm('確定要刪除這個案例嗎？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/cases/delete/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            casesState.cases = casesState.cases.filter(c => c.id !== id);
            filterCases(casesState.currentFilter);
            updateCasesStats();
        }
    } catch (error) {
        console.error('刪除失敗:', error);
        alert('刪除失敗');
    }
}

function viewCase(id) {
    const caseItem = casesState.cases.find(c => c.id === id);
    if (!caseItem) return;
    
    const isQualified = caseItem.profit >= casesState.minProfitThreshold;
    
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h3>案例詳情</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            
            <div class="modal-body">
                <div class="case-detail">
                    <div class="detail-row">
                        <span class="badge ${caseItem.direction.toLowerCase()}">${caseItem.direction}</span>
                        <span class="badge ${isQualified ? 'success' : ''}" style="background: ${isQualified ? '#10b981' : '#f59e0b'};">
                            ${isQualified ? '✓ 合格' : '⚠ 不合格'}
                        </span>
                    </div>
                    
                    <div class="detail-row">
                        <strong>交易對:</strong> ${caseItem.symbol} (${caseItem.timeframe})
                    </div>
                    
                    <div class="detail-row">
                        <strong>槓桿:</strong> ${caseItem.leverage}x
                    </div>
                    
                    <div class="detail-row">
                        <strong>入場價格:</strong> $${caseItem.entry_price.toLocaleString()}
                    </div>
                    
                    <div class="detail-row">
                        <strong>出場價格:</strong> $${caseItem.exit_price.toLocaleString()}
                    </div>
                    
                    <div class="detail-row">
                        <strong>盈虧:</strong> <span class="${caseItem.profit > 0 ? 'positive' : 'negative'}">
                            ${caseItem.profit > 0 ? '+' : ''}${caseItem.profit.toFixed(2)}%
                        </span>
                    </div>
                    
                    <div class="detail-row">
                        <strong>持倉時間:</strong> ${caseItem.holding_hours}h
                    </div>
                    
                    <hr>
                    
                    <div class="detail-row">
                        <strong>入場理由:</strong>
                    </div>
                    <div class="detail-content">${caseItem.reason}</div>
                    
                    ${caseItem.exit_reason ? `
                    <div class="detail-row">
                        <strong>出場理由:</strong>
                    </div>
                    <div class="detail-content">${caseItem.exit_reason}</div>
                    ` : ''}
                    
                    <hr>
                    
                    <div class="detail-row">
                        <strong>技術指標:</strong>
                    </div>
                    <div class="detail-content">
                        <div>RSI: ${caseItem.rsi.toFixed(2)}</div>
                        <div>MACD Hist: ${caseItem.macd_hist.toFixed(4)}</div>
                        <div>ADX: ${caseItem.adx.toFixed(2)}</div>
                        <div>BB Position: ${(caseItem.bb_position * 100).toFixed(1)}%</div>
                        <div>ATR: ${caseItem.atr.toFixed(2)}</div>
                        <div>Volume Ratio: ${caseItem.volume_ratio.toFixed(2)}</div>
                    </div>
                    
                    <hr>
                    
                    <div class="detail-row">
                        <strong>標籤:</strong>
                    </div>
                    <div class="case-tags">
                        ${caseItem.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                    
                    <div class="detail-row" style="margin-top: 16px;">
                        <small>入場時間: ${new Date(caseItem.entry_time).toLocaleString('zh-TW')}</small>
                    </div>
                </div>
            </div>
            
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">關閉</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

document.addEventListener('DOMContentLoaded', initCases);
