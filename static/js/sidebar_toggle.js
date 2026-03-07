/**
 * 側邊欄收納功能
 */

(function() {
    'use strict';
    
    // 狀態管理
    const STORAGE_KEY = 'stw_sidebar_collapsed';
    let isCollapsed = localStorage.getItem(STORAGE_KEY) === 'true';
    
    // 初始化
    function init() {
        createToggleButton();
        createOverlay();
        applyState();
        bindEvents();
        console.log('[SidebarToggle] 初始化完成');
    }
    
    // 創建漢堡按鈕
    function createToggleButton() {
        const button = document.createElement('button');
        button.className = 'sidebar-toggle';
        button.setAttribute('aria-label', '切換側邊欄');
        button.innerHTML = `
            <span></span>
            <span></span>
            <span></span>
        `;
        document.body.appendChild(button);
    }
    
    // 創建遮罩層
    function createOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
    }
    
    // 應用狀態
    function applyState() {
        if (isCollapsed) {
            document.body.classList.add('sidebar-collapsed');
        } else {
            document.body.classList.remove('sidebar-collapsed');
        }
    }
    
    // 切換狀態
    function toggleSidebar() {
        isCollapsed = !isCollapsed;
        localStorage.setItem(STORAGE_KEY, isCollapsed);
        applyState();
        
        console.log(`[SidebarToggle] 側邊欄 ${isCollapsed ? '收起' : '展開'}`);
    }
    
    // 綁定事件
    function bindEvents() {
        // 按鈕點擊
        const toggleBtn = document.querySelector('.sidebar-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', toggleSidebar);
        }
        
        // 遮罩層點擊
        const overlay = document.querySelector('.sidebar-overlay');
        if (overlay) {
            overlay.addEventListener('click', () => {
                if (!isCollapsed) {
                    toggleSidebar();
                }
            });
        }
        
        // 鍵盤快捷鍵: Ctrl+B
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'b') {
                e.preventDefault();
                toggleSidebar();
            }
        });
        
        // 視窗大小變化
        window.addEventListener('resize', handleResize);
    }
    
    // 處理視窗變化
    function handleResize() {
        const width = window.innerWidth;
        
        // 手機版預設收起
        if (width <= 768) {
            if (!isCollapsed) {
                isCollapsed = true;
                applyState();
            }
        }
    }
    
    // DOM 載入完成後執行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
