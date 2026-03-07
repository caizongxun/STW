/**
 * 懸浮球聊天室
 * 在網頁右下角顯示一個懸浮球按鈕
 * 點擊後打開聊天室視窗
 * 
 * 修復: 適配 /api/ai-chat-data 真實返回格式
 */

(function() {
    'use strict';
    
    // 創建懸浮球按鈕
    function createFloatingButton() {
        const button = document.createElement('button');
        button.id = 'floatingChatButton';
        button.className = 'floating-chat-button';
        button.innerHTML = `
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="notification-dot" id="chatNotificationDot" style="display: none;"></span>
        `;
        document.body.appendChild(button);
        return button;
    }
    
    // 創建聊天室視窗
    function createChatWindow() {
        const chatWindow = document.createElement('div');
        chatWindow.id = 'floatingChatWindow';
        chatWindow.className = 'floating-chat-window';
        chatWindow.style.display = 'none';
        
        chatWindow.innerHTML = `
            <div class="chat-window-header">
                <div class="header-left">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    <span>🤖 AI 分析實時對話</span>
                </div>
                <div class="header-right">
                    <button class="minimize-btn" id="minimizeChatBtn" title="最小化">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                    </button>
                    <button class="close-btn" id="closeChatBtn" title="關閉">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="chat-window-content">
                <div class="chat-messages" id="floatingChatMessages">
                    <div class="chat-empty">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                        <p>點擊「獲取實時訊息」後，這裡將顯示所有 AI 模型的完整回應</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(chatWindow);
        return chatWindow;
    }
    
    // 渲染聊天訊息
    function renderChatMessages(apiResponse) {
        const messagesContainer = document.getElementById('floatingChatMessages');
        
        console.log('[FLOATING-CHAT] API Response:', apiResponse);
        
        // 檢查 API 回應
        if (!apiResponse || !apiResponse.success) {
            messagesContainer.innerHTML = `
                <div class="chat-empty">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                    <p>${apiResponse?.message || '點擊「獲取實時訊息」後，這裡將顯示所有 AI 模型的完整回應'}</p>
                </div>
            `;
            return;
        }
        
        const data = apiResponse.data;
        const model_responses = data.model_responses || {};
        
        console.log('[FLOATING-CHAT] Model responses:', model_responses);
        
        if (Object.keys(model_responses).length === 0) {
            messagesContainer.innerHTML = `
                <div class="chat-empty">
                    <p>無模型回應數據</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        // Model A
        if (model_responses.model_a) {
            html += renderModelMessage(
                'MODEL A',
                'badge-model-a',
                'bubble-model-a',
                model_responses.model_a
            );
        }
        
        // Model B
        if (model_responses.model_b) {
            html += renderModelMessage(
                'MODEL B',
                'badge-model-b',
                'bubble-model-b',
                model_responses.model_b
            );
        }
        
        // Arbitrator
        if (model_responses.arbitrator) {
            html += renderModelMessage(
                'ARBITRATOR',
                'badge-arbitrator',
                'bubble-arbitrator',
                model_responses.arbitrator
            );
        }
        
        // Executor
        if (model_responses.executor) {
            html += renderExecutorMessage(model_responses.executor);
        }
        
        // 最終決策
        if (data.final_decision) {
            html += renderFinalDecision(data.final_decision);
        }
        
        messagesContainer.innerHTML = html;
        
        // 滚動到底部
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }
    
    function renderModelMessage(modelName, badgeClass, bubbleClass, modelData) {
        const raw_content = modelData.raw_content || modelData.reasoning || '無詳細說明';
        
        return `
            <div class="chat-message ai-message">
                <div class="message-bubble ${bubbleClass}">
                    <div class="message-header">
                        <span class="model-badge ${badgeClass}">${modelName}</span>
                        <span class="timestamp">${new Date().toLocaleTimeString('zh-TW', {hour: '2-digit', minute: '2-digit'})}</span>
                    </div>
                    <div class="message-content">
                        <div class="decision-summary">
                            <div class="decision-row">
                                <span class="decision-label">動作:</span>
                                <span class="decision-value action-${modelData.action || 'UNKNOWN'}">${modelData.action || '未知'}</span>
                            </div>
                            <div class="decision-row">
                                <span class="decision-label">信心度:</span>
                                <span class="decision-value">${modelData.confidence || 0}%</span>
                            </div>
                        </div>
                        <div class="reasoning">
                            ${formatContent(raw_content)}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    function renderExecutorMessage(executorData) {
        const raw_content = executorData.raw_content || executorData.reasoning || '無詳細說明';
        
        return `
            <div class="chat-message ai-message">
                <div class="message-bubble bubble-executor">
                    <div class="message-header">
                        <span class="model-badge badge-executor">EXECUTOR</span>
                        <span class="timestamp">${new Date().toLocaleTimeString('zh-TW', {hour: '2-digit', minute: '2-digit'})}</span>
                    </div>
                    <div class="message-content">
                        <div class="decision-summary">
                            <div class="decision-row">
                                <span class="decision-label">執行決策:</span>
                                <span class="decision-value">${executorData.execution_decision || '未知'}</span>
                            </div>
                            <div class="decision-row">
                                <span class="decision-label">最終動作:</span>
                                <span class="decision-value action-${executorData.final_action || 'UNKNOWN'}">${executorData.final_action || '未知'}</span>
                            </div>
                            <div class="decision-row">
                                <span class="decision-label">信心度:</span>
                                <span class="decision-value">${executorData.adjusted_confidence || 0}%</span>
                            </div>
                        </div>
                        <div class="reasoning">
                            ${formatContent(raw_content)}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    function renderFinalDecision(decision) {
        return `
            <div class="chat-message final-decision">
                <div class="message-bubble">
                    <div class="message-header">
                        <span class="model-badge badge-final">✅ 最終決策</span>
                    </div>
                    <div class="message-content">
                        <div class="decision-summary" style="background: linear-gradient(135deg, rgba(46, 204, 113, 0.1), rgba(39, 174, 96, 0.1));">
                            <div class="decision-row">
                                <span class="decision-label">動作:</span>
                                <span class="decision-value action-${decision.action || 'UNKNOWN'}">${decision.action || '未知'}</span>
                            </div>
                            <div class="decision-row">
                                <span class="decision-label">信心度:</span>
                                <span class="decision-value">${decision.confidence || 0}%</span>
                            </div>
                            ${decision.execution_decision ? `
                            <div class="decision-row">
                                <span class="decision-label">執行狀態:</span>
                                <span class="decision-value">${decision.execution_decision}</span>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    function formatContent(content) {
        if (!content) return '無內容';
        
        // 保留換行和空格
        return content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>');
    }
    
    // 初始化
    function init() {
        const button = createFloatingButton();
        const chatWindow = createChatWindow();
        
        let isOpen = false;
        
        // 懸浮球點擊事件
        button.addEventListener('click', () => {
            if (isOpen) {
                closeChatWindow();
            } else {
                openChatWindow();
            }
        });
        
        // 關閉按鈕
        document.getElementById('closeChatBtn').addEventListener('click', closeChatWindow);
        
        // 最小化按鈕
        document.getElementById('minimizeChatBtn').addEventListener('click', closeChatWindow);
        
        function openChatWindow() {
            chatWindow.style.display = 'flex';
            setTimeout(() => {
                chatWindow.classList.add('open');
                button.classList.add('active');
            }, 10);
            isOpen = true;
            
            // 隱藏通知點
            const notificationDot = document.getElementById('chatNotificationDot');
            if (notificationDot) {
                notificationDot.style.display = 'none';
            }
            
            // 加載最新數據
            loadChatData();
        }
        
        function closeChatWindow() {
            chatWindow.classList.remove('open');
            button.classList.remove('active');
            setTimeout(() => {
                chatWindow.style.display = 'none';
            }, 300);
            isOpen = false;
        }
        
        // 加載聊天數據
        async function loadChatData() {
            try {
                console.log('[FLOATING-CHAT] Loading chat data...');
                const response = await fetch('/api/ai-chat-data');
                const data = await response.json();
                console.log('[FLOATING-CHAT] Received data:', data);
                renderChatMessages(data);
            } catch (error) {
                console.error('[FLOATING-CHAT] 加載聊天數據失敗:', error);
                const messagesContainer = document.getElementById('floatingChatMessages');
                messagesContainer.innerHTML = `
                    <div class="chat-empty">
                        <p>加載失敗: ${error.message}</p>
                    </div>
                `;
            }
        }
        
        // 監聽 AI 分析完成事件
        window.addEventListener('aiAnalysisComplete', () => {
            console.log('[FLOATING-CHAT] AI analysis complete event received');
            
            // 顯示通知點
            const notificationDot = document.getElementById('chatNotificationDot');
            if (notificationDot && !isOpen) {
                notificationDot.style.display = 'block';
            }
            
            // 如果聊天室已打開，自動更新
            if (isOpen) {
                loadChatData();
            }
        });
    }
    
    // DOM 加載完成後初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
