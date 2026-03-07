/**
 * AI 聊天室功能
 * 在分析後顯示所有 AI 模型的完整回應
 */

let aiChatUpdateInterval = null;

/**
 * 初始化 AI 聊天室
 */
function initAIChat() {
    const toggleBtn = document.getElementById('aiChatToggle');
    const panel = document.getElementById('aiChatPanel');
    
    if (toggleBtn && panel) {
        toggleBtn.addEventListener('click', () => {
            panel.classList.toggle('collapsed');
            toggleBtn.textContent = panel.classList.contains('collapsed') ? '展開' : '收起';
        });
    }
}

/**
 * 加載 AI 聊天室數據
 */
async function loadAIChatData() {
    try {
        const response = await fetch('/api/ai-chat-data');
        const data = await response.json();
        
        if (data.success && data.data) {
            renderAIChatPanel(data.data);
            
            // 顯示 Panel
            const panel = document.getElementById('aiChatPanel');
            if (panel) {
                panel.style.display = 'block';
            }
        } else {
            console.log('No AI chat data available:', data.message);
        }
    } catch (error) {
        console.error('Failed to load AI chat data:', error);
    }
}

/**
 * 渲染 AI 聊天室 Panel
 */
function renderAIChatPanel(data) {
    renderAIResponses(data);
    renderPromptInfo(data);
}

/**
 * 渲染 AI 回應區域
 */
function renderAIResponses(data) {
    const container = document.getElementById('aiResponsesContainer');
    if (!container) return;
    
    container.innerHTML = '';
    const responses = data.model_responses || {};
    
    // Model A
    if (responses.model_a) {
        container.innerHTML += createMessageBubble(
            'Model A',
            responses.model_a.model_name || 'Unknown',
            responses.model_a.raw_content || responses.model_a.reasoning || '無內容',
            'model-a'
        );
    }
    
    // Model B
    if (responses.model_b) {
        container.innerHTML += createMessageBubble(
            'Model B',
            responses.model_b.model_name || 'Unknown',
            responses.model_b.raw_content || responses.model_b.reasoning || '無內容',
            'model-b'
        );
    }
    
    // Arbitrator
    if (responses.arbitrator) {
        container.innerHTML += createMessageBubble(
            'Arbitrator',
            responses.arbitrator.model_name || 'Unknown',
            responses.arbitrator.raw_content || responses.arbitrator.reasoning || '無內容',
            'arbitrator'
        );
    }
    
    // Executor
    if (responses.executor) {
        container.innerHTML += createMessageBubble(
            'Executor',
            '執行審核員',
            responses.executor.raw_content || responses.executor.reasoning || '無內容',
            'executor'
        );
    }
    
    if (Object.keys(responses).length === 0) {
        container.innerHTML = '<p class="ai-chat-empty">無 AI 回應數據</p>';
    }
}

/**
 * 創建訊息泡泡
 */
function createMessageBubble(label, modelName, content, type) {
    return `
        <div class="chat-message">
            <div class="message-header">
                <span class="model-badge badge-${type}">${label}</span>
                <span class="timestamp">${modelName}</span>
            </div>
            <div class="message-bubble bubble-${type}">
                ${escapeHtml(content)}
            </div>
        </div>
    `;
}

/**
 * 渲染 Prompt 資訊區域
 */
function renderPromptInfo(data) {
    const container = document.getElementById('aiPromptContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    // 決策摘要
    const responses = data.model_responses || {};
    const finalDecision = responses.executor || responses.arbitrator || responses.model_a || {};
    
    container.innerHTML += `
        <div class="decision-summary">
            <div class="prompt-title">最終決策</div>
            <div class="decision-row">
                <span class="decision-label">Action</span>
                <span class="decision-value action-${finalDecision.final_action || finalDecision.action || 'HOLD'}">
                    ${finalDecision.final_action || finalDecision.action || 'HOLD'}
                </span>
            </div>
            <div class="decision-row">
                <span class="decision-label">Confidence</span>
                <span class="decision-value">${finalDecision.adjusted_confidence || finalDecision.confidence || 0}%</span>
            </div>
            ${finalDecision.execution_decision ? `
            <div class="decision-row">
                <span class="decision-label">Execution</span>
                <span class="decision-value">${finalDecision.execution_decision}</span>
            </div>
            ` : ''}
        </div>
    `;
    
    // System Prompt
    if (data.system_prompt) {
        const preview = data.system_prompt.substring(0, 500);
        container.innerHTML += `
            <div class="prompt-section">
                <div class="prompt-title">System Prompt</div>
                <div class="code-block">
                    <pre>${escapeHtml(preview)}...</pre>
                </div>
            </div>
        `;
    }
    
    // User Prompt
    if (data.user_prompt) {
        const userPrompt = data.user_prompt;
        const preview = userPrompt.length > 1000 ? userPrompt.substring(0, 1000) + '...' : userPrompt;
        
        container.innerHTML += `
            <div class="prompt-section">
                <div class="prompt-title">User Prompt</div>
                <div class="code-block">
                    <pre>${escapeHtml(preview)}</pre>
                </div>
            </div>
        `;
    }
}

/**
 * HTML 轉義
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 啟動自動更新
 */
function startAIChatAutoUpdate() {
    if (aiChatUpdateInterval) {
        clearInterval(aiChatUpdateInterval);
    }
    
    // 每 30 秒更新一次
    aiChatUpdateInterval = setInterval(() => {
        loadAIChatData();
    }, 30000);
}

/**
 * 停止自動更新
 */
function stopAIChatAutoUpdate() {
    if (aiChatUpdateInterval) {
        clearInterval(aiChatUpdateInterval);
        aiChatUpdateInterval = null;
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initAIChat();
    
    // 在分析按鈕點擊後加載 AI 聊天室數據
    const originalAnalyzeBtn = document.getElementById('analyzeBtn');
    if (originalAnalyzeBtn) {
        originalAnalyzeBtn.addEventListener('click', () => {
            // 等待 2 秒後加載 AI 聊天室數據
            setTimeout(() => {
                loadAIChatData();
            }, 2000);
        });
    }
    
    // 啟動自動更新
    startAIChatAutoUpdate();
});

// 頁面關閉時停止自動更新
window.addEventListener('beforeunload', () => {
    stopAIChatAutoUpdate();
});
