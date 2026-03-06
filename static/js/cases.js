/**
 * 學習案例庫 JavaScript
 * 管理成功交易案例，供 AI 學習
 */

const casesState = {
    cases: [],
    filteredCases: [],
    currentFilter: 'all'
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
}

function setupCasesListeners() {
    casesElements.filterAll.addEventListener('click', () => filterCases('all'));
    casesElements.filterLong.addEventListener('click', () => filterCases('long'));
    casesElements.filterShort.addEventListener('click', () => filterCases('short'));
    casesElements.addCaseBtn.addEventListener('click', showAddCaseModal);
    casesElements.searchInput.addEventListener('input', searchCases);
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
    
    // 更新按鈕狀態
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
    
    casesElements.casesList.innerHTML = casesState.filteredCases.map(caseItem => `
        <div class="case-card" data-id="${caseItem.id}">
            <div class="case-header">
                <div class="case-title">
                    <span class="badge ${caseItem.direction.toLowerCase()}">${caseItem.direction}</span>
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
                    <div><strong>時間:</strong> ${new Date(caseItem.timestamp).toLocaleString('zh-TW')}</div>
                </div>
                
                <div class="case-reason">
                    <strong>理由:</strong> ${caseItem.reason}
                </div>
                
                <div class="case-indicators">
                    <small>
                        RSI: ${caseItem.rsi.toFixed(2)} | 
                        MACD: ${caseItem.macd_hist.toFixed(4)} | 
                        ADX: ${caseItem.adx.toFixed(2)}
                    </small>
                </div>
                
                <div class="case-tags">
                    ${caseItem.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            </div>
            
            <div class="case-actions">
                <button class="btn-sm btn-secondary" onclick="viewCase('${caseItem.id}')">檢視</button>
                <button class="btn-sm btn-danger" onclick="deleteCase('${caseItem.id}')">刪除</button>
            </div>
        </div>
    `).join('');
}

function updateCasesStats() {
    const total = casesState.cases.length;
    casesElements.totalCases.textContent = total;
    
    if (total === 0) {
        casesElements.avgProfit.textContent = '0%';
        casesElements.winRate.textContent = '0%';
        return;
    }
    
    const avgProfit = casesState.cases.reduce((sum, c) => sum + c.profit, 0) / total;
    casesElements.avgProfit.textContent = `${avgProfit > 0 ? '+' : ''}${avgProfit.toFixed(2)}%`;
    
    const wins = casesState.cases.filter(c => c.profit > 0).length;
    const winRate = (wins / total) * 100;
    casesElements.winRate.textContent = `${winRate.toFixed(1)}%`;
}

function showAddCaseModal() {
    // TODO: 顯示添加案例的對話框
    alert('添加案例功能還在開發中...');
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
    if (caseItem) {
        // TODO: 顯示案例詳情
        console.log('View case:', caseItem);
        alert('檢視案例功能還在開發中...');
    }
}

document.addEventListener('DOMContentLoaded', initCases);
