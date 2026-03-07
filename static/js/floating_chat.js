/**
 * 懸浮球聊天室
 * 在網頁右下角顯示一個懸浮球按鈕
 * 點擊後打開聊天室視窗
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
                        <p>點擊「獲取實時訊號」後，這裡將顯示所有 AI 模型的完整回應</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(chatWindow);
        return chatWindow;
    }
    
    // 渲染聊天訊息
    function renderChatMessages(data) {
        const messagesContainer = document.getElementById('floatingChatMessages');
        
        if (!data || !data.models || data.models.length === 0) {
            messagesContainer.innerHTML = `
                <div class="chat-empty">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                    <p>點擊「獲取實時訊號」後，這裡將顯示所有 AI 模型的完整回應</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        // 顯示 Prompt (用戶視角)
        if (data.prompt_info) {
            html += `
                <div class="chat-message user-message">
                    <div class="message-bubble">
                        <div class="message-header">
                            <span class="message-author">👤 系統 Prompt</span>
                            <span class="message-time">${new Date().toLocaleTimeString('zh-TW', {hour: '2-digit', minute: '2-digit'})}</span>
                        </div>
                        <div class="message-content">
                            <strong>市場數據:</strong><br>
                            交易對: ${data.prompt_info.symbol || 'N/A'}<br>
                            現價: $${data.prompt_info.price ? data.prompt_info.price.toLocaleString() : 'N/A'}<br>
                            RSI: ${data.prompt_info.rsi || 'N/A'}<br>
                            MACD: ${data.prompt_info.macd_hist || 'N/A'}
                        </div>
                    </div>
                </div>
            `;
        }
        
        // 顯示每個模型的回應
        data.models.forEach(model => {
            const messageClass = getMessageClass(model.stage);
            const badgeClass = getBadgeClass(model.stage);
            
            html += `
                <div class="chat-message ai-message ${messageClass}">
                    <div class="message-bubble">
                        <div class="message-header">
                            <span class="model-badge ${badgeClass}">${model.name}</span>
                            <span class="message-time">${model.duration || '0.0s'}</span>
                        </div>
                        <div class="message-content">
                            <div class="decision-summary">
                                <div class="decision-row">
                                    <span class="decision-label">動作:</span>
                                    <span class="decision-value action-${model.action}">${model.action}</span>
                                </div>
                                <div class="decision-row">
                                    <span class="decision-label">信心度:</span>
                                    <span class="decision-value">${model.confidence}%</span>
                                </div>
                            </div>
                            <div class="reasoning">
                                ${model.reasoning || '無詳細說明'}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        // 最終決策
        if (data.final_decision) {
            html += `
                <div class="chat-message final-decision">
                    <div class="message-bubble">
                        <div class="message-header">
                            <span class="model-badge badge-final">✅ 最終決策</span>
                        </div>
                        <div class="message-content">
                            <div class="decision-summary" style="background: linear-gradient(135deg, rgba(46, 204, 113, 0.1), rgba(39, 174, 96, 0.1));">
                                <div class="decision-row">
                                    <span class="decision-label">動作:</span>
                                    <span class="decision-value action-${data.final_decision.action}">${data.final_decision.action}</span>
                                </div>
                                <div class="decision-row">
                                    <span class="decision-label">信心度:</span>
                                    <span class="decision-value">${data.final_decision.confidence}%</span>
                                </div>
                                ${data.final_decision.execution_decision ? `
                                <div class="decision-row">
                                    <span class="decision-label">執行狀態:</span>
                                    <span class="decision-value">${data.final_decision.execution_decision}</span>
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        messagesContainer.innerHTML = html;
        
        // 滾動到底部
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }
    
    function getMessageClass(stage) {
        const classes = {
            'model_a': 'message-model-a',
            'model_b': 'message-model-b',
            'arbitrator': 'message-arbitrator',
            'executor': 'message-executor'
        };
        return classes[stage] || '';
    }
    
    function getBadgeClass(stage) {
        const classes = {
            'model_a': 'badge-model-a',
            'model_b': 'badge-model-b',
            'arbitrator': 'badge-arbitrator',
            'executor': 'badge-executor'
        };
        return classes[stage] || 'badge-model-a';
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
                const response = await fetch('/api/ai-chat-data');
                const data = await response.json();
                renderChatMessages(data);
            } catch (error) {
                console.error('加載聊天數據失敗:', error);
            }
        }
        
        // 監聽 AI 分析完成事件
        window.addEventListener('aiAnalysisComplete', () => {
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
