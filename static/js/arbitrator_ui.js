/**
 * 兩階段仲裁決策 UI
 * 顯示每個模型的分析結果
 */

class ArbitratorUI {
    constructor() {
        this.initUI();
    }
    
    initUI() {
        // 在 AI 分析結果區域添加兩階段顯示
        const aiResultDiv = document.getElementById('ai-result');
        
        if (!aiResultDiv) return;
        
        // 創建兩階段顯示區域
        const arbitratorSection = document.createElement('div');
        arbitratorSection.id = 'arbitrator-section';
        arbitratorSection.className = 'arbitrator-section hidden';
        arbitratorSection.innerHTML = `
            <div class="stage-header">
                <h3>🧠 兩階段仲裁決策</h3>
            </div>
            
            <!-- 階段 1: 兩個快速模型 -->
            <div class="stage-1">
                <div class="stage-title">
                    <span class="stage-badge">階段 1</span>
                    <span>兩個快速模型分析</span>
                </div>
                
                <div class="models-grid">
                    <!-- Model A -->
                    <div class="model-result" id="model-a-result">
                        <div class="model-header">
                            <span class="model-icon">🤖</span>
                            <span class="model-name" id="model-a-name">Model A</span>
                            <span class="model-time" id="model-a-time">0s</span>
                        </div>
                        <div class="model-decision">
                            <div class="decision-action" id="model-a-action">-</div>
                            <div class="decision-confidence" id="model-a-confidence">-</div>
                        </div>
                        <div class="model-reasoning" id="model-a-reasoning">
                            分析中...
                        </div>
                    </div>
                    
                    <!-- Model B -->
                    <div class="model-result" id="model-b-result">
                        <div class="model-header">
                            <span class="model-icon">🤖</span>
                            <span class="model-name" id="model-b-name">Model B</span>
                            <span class="model-time" id="model-b-time">0s</span>
                        </div>
                        <div class="model-decision">
                            <div class="decision-action" id="model-b-action">-</div>
                            <div class="decision-confidence" id="model-b-confidence">-</div>
                        </div>
                        <div class="model-reasoning" id="model-b-reasoning">
                            分析中...
                        </div>
                    </div>
                </div>
                
                <!-- 共識狀態 -->
                <div class="consensus-status" id="consensus-status">
                    <span class="status-icon">⏳</span>
                    <span class="status-text">等待分析結果...</span>
                </div>
            </div>
            
            <!-- 階段 2: 仲裁者 (只在分歧時顯示) -->
            <div class="stage-2 hidden" id="stage-2">
                <div class="stage-title">
                    <span class="stage-badge">階段 2</span>
                    <span>仲裁者最終決策</span>
                </div>
                
                <div class="arbitrator-result" id="arbitrator-result">
                    <div class="model-header">
                        <span class="model-icon">🧠</span>
                        <span class="model-name" id="arbitrator-name">Arbitrator</span>
                        <span class="model-time" id="arbitrator-time">0s</span>
                    </div>
                    <div class="arbitrator-analysis" id="arbitrator-analysis">
                        仲裁中...
                    </div>
                </div>
            </div>
            
            <!-- 最終決策 -->
            <div class="final-decision" id="final-decision">
                <div class="decision-title">✅ 最終決策</div>
                <div class="decision-content">
                    <div class="decision-main">
                        <div class="action-badge" id="final-action">-</div>
                        <div class="confidence-badge" id="final-confidence">-</div>
                    </div>
                    <div class="decision-details" id="final-details">
                        <div class="detail-row">
                            <span class="label">進場:</span>
                            <span class="value" id="final-entry">-</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">止損:</span>
                            <span class="value" id="final-stop-loss">-</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">止盈:</span>
                            <span class="value" id="final-take-profit">-</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">風險收益比:</span>
                            <span class="value" id="final-risk-reward">-</span>
                        </div>
                    </div>
                    <div class="decision-source" id="final-source">
                        決策來源: -
                    </div>
                </div>
            </div>
        `;
        
        // 插入到 AI 結果區域
        aiResultDiv.insertBefore(arbitratorSection, aiResultDiv.firstChild);
        
        // 添加 CSS
        this.addStyles();
    }
    
    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .arbitrator-section {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .stage-header h3 {
                color: white;
                margin: 0 0 20px 0;
                font-size: 24px;
                text-align: center;
            }
            
            .stage-title {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 15px;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            
            .stage-badge {
                background: rgba(255,255,255,0.2);
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 14px;
            }
            
            .models-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 15px;
            }
            
            .model-result {
                background: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .model-header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 10px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e0e0e0;
            }
            
            .model-icon {
                font-size: 24px;
            }
            
            .model-name {
                flex: 1;
                font-weight: bold;
                color: #333;
            }
            
            .model-time {
                color: #666;
                font-size: 12px;
                background: #f0f0f0;
                padding: 3px 8px;
                border-radius: 10px;
            }
            
            .model-decision {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
            }
            
            .decision-action {
                font-size: 20px;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 6px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .decision-action.OPEN_LONG { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
            .decision-action.OPEN_SHORT { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
            .decision-action.CLOSE { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
            .decision-action.HOLD { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
            
            .decision-confidence {
                font-size: 18px;
                color: #666;
                padding: 5px 10px;
            }
            
            .model-reasoning {
                font-size: 14px;
                color: #555;
                line-height: 1.6;
                padding: 10px;
                background: #f9f9f9;
                border-radius: 6px;
                max-height: 120px;
                overflow-y: auto;
            }
            
            .consensus-status {
                background: white;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                font-size: 16px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            
            .consensus-status.agreement {
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                color: white;
            }
            
            .consensus-status.disagreement {
                background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
                color: white;
            }
            
            .stage-2 {
                margin-top: 20px;
            }
            
            .arbitrator-result {
                background: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .arbitrator-analysis {
                font-size: 14px;
                color: #555;
                line-height: 1.6;
                padding: 15px;
                background: #f9f9f9;
                border-radius: 6px;
            }
            
            .final-decision {
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            
            .decision-title {
                font-size: 20px;
                font-weight: bold;
                color: #333;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e0e0e0;
            }
            
            .decision-main {
                display: flex;
                gap: 20px;
                margin-bottom: 15px;
            }
            
            .action-badge {
                font-size: 24px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .confidence-badge {
                font-size: 24px;
                padding: 10px 20px;
                border-radius: 8px;
                background: #f0f0f0;
                color: #333;
            }
            
            .decision-details {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin-bottom: 15px;
            }
            
            .detail-row {
                display: flex;
                justify-content: space-between;
                padding: 8px;
                background: #f9f9f9;
                border-radius: 6px;
            }
            
            .detail-row .label {
                color: #666;
                font-weight: bold;
            }
            
            .detail-row .value {
                color: #333;
                font-weight: bold;
            }
            
            .decision-source {
                text-align: center;
                padding: 10px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            
            .hidden { display: none; }
            
            @media (max-width: 768px) {
                .models-grid {
                    grid-template-columns: 1fr;
                }
                
                .decision-details {
                    grid-template-columns: 1fr;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    updateModelA(data) {
        document.getElementById('model-a-name').textContent = data.model || 'Model A';
        document.getElementById('model-a-time').textContent = `${(data.elapsed || 0).toFixed(1)}s`;
        
        const actionEl = document.getElementById('model-a-action');
        actionEl.textContent = data.action || '-';
        actionEl.className = `decision-action ${data.action || ''}`;
        
        document.getElementById('model-a-confidence').textContent = data.confidence ? `${data.confidence}%` : '-';
        document.getElementById('model-a-reasoning').textContent = data.reasoning || '分析中...';
    }
    
    updateModelB(data) {
        document.getElementById('model-b-name').textContent = data.model || 'Model B';
        document.getElementById('model-b-time').textContent = `${(data.elapsed || 0).toFixed(1)}s`;
        
        const actionEl = document.getElementById('model-b-action');
        actionEl.textContent = data.action || '-';
        actionEl.className = `decision-action ${data.action || ''}`;
        
        document.getElementById('model-b-confidence').textContent = data.confidence ? `${data.confidence}%` : '-';
        document.getElementById('model-b-reasoning').textContent = data.reasoning || '分析中...';
    }
    
    updateConsensusStatus(agreed, actionA, actionB) {
        const statusEl = document.getElementById('consensus-status');
        
        if (agreed) {
            statusEl.className = 'consensus-status agreement';
            statusEl.innerHTML = `
                <span class="status-icon">✅</span>
                <span class="status-text">兩個模型同意: ${actionA}</span>
            `;
        } else {
            statusEl.className = 'consensus-status disagreement';
            statusEl.innerHTML = `
                <span class="status-icon">⚠️</span>
                <span class="status-text">意見分歧: ${actionA} vs ${actionB} → 需要仲裁</span>
            `;
        }
    }
    
    showArbitrator() {
        document.getElementById('stage-2').classList.remove('hidden');
    }
    
    updateArbitrator(data) {
        document.getElementById('arbitrator-name').textContent = data.model || 'Arbitrator';
        document.getElementById('arbitrator-time').textContent = `${(data.elapsed || 0).toFixed(1)}s`;
        document.getElementById('arbitrator-analysis').textContent = data.reasoning || '仲裁中...';
    }
    
    updateFinalDecision(data, source) {
        document.getElementById('final-action').textContent = data.action || '-';
        document.getElementById('final-action').className = `action-badge ${data.action || ''}`;
        document.getElementById('final-confidence').textContent = data.confidence ? `${data.confidence}%` : '-';
        
        document.getElementById('final-entry').textContent = data.entry_price ? `$${data.entry_price.toFixed(2)}` : '-';
        document.getElementById('final-stop-loss').textContent = data.stop_loss ? `$${data.stop_loss.toFixed(2)}` : '-';
        document.getElementById('final-take-profit').textContent = data.take_profit ? `$${data.take_profit.toFixed(2)}` : '-';
        document.getElementById('final-risk-reward').textContent = data.risk_reward_ratio ? `1:${data.risk_reward_ratio.toFixed(1)}` : '-';
        
        document.getElementById('final-source').textContent = `決策來源: ${source}`;
    }
    
    show() {
        document.getElementById('arbitrator-section').classList.remove('hidden');
    }
    
    hide() {
        document.getElementById('arbitrator-section').classList.add('hidden');
    }
    
    reset() {
        // 重置所有顯示
        this.updateModelA({ action: '-', confidence: null, reasoning: '分析中...', elapsed: 0 });
        this.updateModelB({ action: '-', confidence: null, reasoning: '分析中...', elapsed: 0 });
        
        const statusEl = document.getElementById('consensus-status');
        statusEl.className = 'consensus-status';
        statusEl.innerHTML = `
            <span class="status-icon">⏳</span>
            <span class="status-text">等待分析結果...</span>
        `;
        
        document.getElementById('stage-2').classList.add('hidden');
        
        this.updateFinalDecision({
            action: '-',
            confidence: null,
            entry_price: null,
            stop_loss: null,
            take_profit: null,
            risk_reward_ratio: null
        }, '-');
    }
}

// 初始化
 const arbitratorUI = new ArbitratorUI();

// 暴露到全局
window.arbitratorUI = arbitratorUI;
