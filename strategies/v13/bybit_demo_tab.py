"""
Bybit 自動交易 UI
支援 Demo Trading / Testnet / Mainnet
整合倉位感知 AI
"""
import streamlit as st
import time
from datetime import datetime
import traceback
import sys
import io

from core.bybit_trader import BybitDemoTrader
from core.data_loader import DataLoader
from core.llm_agent_position_aware import PositionAwareDeepSeekAgent


def render_bybit_demo_tab():
    """渲柔 Bybit 交易頁面"""
    st.subheader("[BYBIT] 智能自動交易")
    
    st.info("""
    **智能特性**：
    - AI 能讀取當前倉位、本金、浮盈浮虧
    - 根據市場波動度動態調整槓框 (1-10x)
    - 支援多種操作：開倉/平倉/加倉/減倉/觀望
    - 智能風控：不超過可用餘額的 30%
    """)
    
    # === 模式選擇 ===
    mode = st.radio(
        "選擇交易模式",
        ['demo', 'testnet', 'mainnet'],
        format_func=lambda x: {
            'demo': '[DEMO] Demo Trading - 真實市場模擬 (推薦)',
            'testnet': '[TEST] Testnet - 測試網 (內部價格)',
            'mainnet': '[LIVE] Mainnet - 真實盤 (危險)'
        }[x],
        horizontal=True,
        key='bybit_mode'
    )
    
    # 模式說明
    if mode == 'demo':
        st.success("""
        **[DEMO] Demo Trading**
        - 使用**真實市場價格**和滑點
        - 模擬資金，不會影響真實資產
        - 適合策略驗證和實戰測試
        - API Endpoint: `api-demo.bybit.com`
        """)
    elif mode == 'testnet':
        st.info("""
        **[TEST] Testnet**
        - 使用**內部模擬價格**
        - 適合開發測試，不適合策略驗證
        - API Endpoint: `api-testnet.bybit.com`
        """)
    else:
        st.error("""
        **[LIVE] Mainnet - 真實盤**
        - 使用真實資金，會實際交易
        - 建議先在 Demo Trading 測試 2-4 週
        - 確認策略勝率 > 60% 再使用
        """)
    
    st.divider()
    
    # === 設定區 ===
    with st.expander("[SETUP] API 設定", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            api_key = st.text_input(
                f"Bybit {mode.upper()} API Key",
                type="password",
                help={
                    'demo': "在 bybit.com 申請 (API Management > Demo Trading)",
                    'testnet': "在 testnet.bybit.com 申請",
                    'mainnet': "在 bybit.com 申請 (真實盤)"
                }[mode],
                key='bybit_api_key'
            )
            
            symbol = st.selectbox(
                "交易對",
                ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT'],
                key='bybit_symbol'
            )
        
        with col2:
            api_secret = st.text_input(
                f"Bybit {mode.upper()} API Secret",
                type="password",
                key='bybit_api_secret'
            )
            
            max_leverage = st.slider(
                "最大槓框倍數",
                1, 10, 5,
                help="AI 會根據市場情況動態調整，不超過此值",
                key='bybit_max_leverage'
            )
        
        update_interval = st.selectbox(
            "更新間隔",
            [('15 分鐘', 15), ('30 分鐘', 30), ('1 小時', 60)],
            format_func=lambda x: x[0],
            key='bybit_update_interval'
        )[1]
        
        ai_confidence_min = st.slider(
            "AI 最低信心度 (%)",
            50, 95, 70, 5,
            key='bybit_ai_confidence'
        )
    
    # === 控制按鈕 ===
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("[TEST] 測試連線", type="secondary", key='bybit_test_btn'):
            if not api_key or not api_secret:
                st.error("[ERROR] 請先輸入 API Key 和 Secret")
            else:
                with st.spinner(f"正在連線 Bybit {mode.upper()}..."):
                    # 捕捉 print 輸出
                    debug_output = io.StringIO()
                    old_stdout = sys.stdout
                    sys.stdout = debug_output
                    
                    try:
                        trader = BybitDemoTrader(
                            api_key=api_key,
                            api_secret=api_secret,
                            demo_mode=mode,
                            symbol=symbol,
                            max_leverage=max_leverage
                        )
                        
                        balance = trader.get_balance()
                        
                        # 恢復 stdout
                        sys.stdout = old_stdout
                        debug_text = debug_output.getvalue()
                        
                        # 顯示 debug 輸出
                        if debug_text:
                            with st.expander("[DEBUG] 詳細訊息"):
                                st.code(debug_text, language="text")
                        
                        if balance['total_equity'] > 0:
                            mode_name = trader.get_account_summary()['mode']
                            st.success(f"[OK] {mode_name} 連線成功! 餘額: ${balance['total_equity']:,.2f} USDT")
                            st.session_state['bybit_trader'] = trader
                        else:
                            if mode == 'demo':
                                st.warning("[WARNING] 連線成功但餘額為 0，請到 bybit.com > Assets > Demo Trading 領取模擬資金")
                            elif mode == 'testnet':
                                st.warning("[WARNING] 連線成功但餘額為 0，請到 testnet.bybit.com 領取模擬資金")
                            else:
                                st.error("[ERROR] 餘額不足，請充值")
                            
                    except Exception as e:
                        sys.stdout = old_stdout
                        debug_text = debug_output.getvalue()
                        
                        if debug_text:
                            with st.expander("[DEBUG] 詳細訊息"):
                                st.code(debug_text, language="text")
                        
                        st.error(f"[ERROR] 連線失敗: {e}")
                        st.code(traceback.format_exc())
    
    with col_btn2:
        start_btn = st.button("[START] 啟動智能交易", type="primary", key='bybit_start_btn')
    
    with col_btn3:
        if st.button("[STOP] 停止交易", type="secondary", key='bybit_stop_btn'):
            st.session_state['bybit_running'] = False
    
    st.divider()
    
    # === 啟動自動交易 ===
    if start_btn:
        if not api_key or not api_secret:
            st.error("[ERROR] 請先輸入 API Key 和 Secret")
        elif mode == 'mainnet':
            st.error("[WARNING] 你正在啟動真實盤交易！請確認你已充分測試策略。")
            if st.checkbox("我了解風險，確認啟動真實盤交易", key='bybit_mainnet_confirm'):
                st.session_state['bybit_running'] = True
                st.session_state['bybit_config'] = {
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'demo_mode': mode,
                    'symbol': symbol,
                    'max_leverage': max_leverage,
                    'update_interval': update_interval,
                    'ai_confidence_min': ai_confidence_min
                }
        else:
            st.session_state['bybit_running'] = True
            st.session_state['bybit_config'] = {
                'api_key': api_key,
                'api_secret': api_secret,
                'demo_mode': mode,
                'symbol': symbol,
                'max_leverage': max_leverage,
                'update_interval': update_interval,
                'ai_confidence_min': ai_confidence_min
            }
    
    # === 自動交易循環 ===
    if st.session_state.get('bybit_running'):
        config = st.session_state['bybit_config']
        
        # 初始化交易器
        if 'bybit_trader' not in st.session_state:
            trader = BybitDemoTrader(
                api_key=config['api_key'],
                api_secret=config['api_secret'],
                demo_mode=config['demo_mode'],
                symbol=config['symbol'],
                max_leverage=config['max_leverage']
            )
            st.session_state['bybit_trader'] = trader
        else:
            trader = st.session_state['bybit_trader']
        
        # 初始化 AI 引擎
        if 'bybit_ai_agent' not in st.session_state:
            st.session_state['bybit_ai_agent'] = PositionAwareDeepSeekAgent()
        
        ai_agent = st.session_state['bybit_ai_agent']
        data_loader = DataLoader()
        
        # 實時顯示區
        status_placeholder = st.empty()
        info_placeholder = st.empty()
        trades_placeholder = st.empty()
        
        # 初始化計時器
        if 'last_update_time' not in st.session_state:
            st.session_state['last_update_time'] = 0
        
        # 導入 prepare_market_features (延遲導入避免循環)
        from strategies.v13 import prepare_market_features
        
        while st.session_state.get('bybit_running'):
            current_time = time.time()
            elapsed_minutes = (current_time - st.session_state['last_update_time']) / 60
            
            # 檢查是否需要更新
            if elapsed_minutes >= config['update_interval']:
                st.session_state['last_update_time'] = current_time
                
                with status_placeholder.container():
                    st.info(f"[UPDATE] {datetime.now().strftime('%H:%M:%S')} - 正在獲取 AI 訊號...")
                
                try:
                    # 1. 獲取最新市場數據
                    df = data_loader.load_data(config['symbol'], '15m')
                    
                    if df is not None and len(df) > 200:
                        # 2. 計算技術指標
                        market_data = prepare_market_features(df.iloc[-1], df)
                        
                        # 3. 獲取帳戶資訊
                        account_info = trader.get_account_info()
                        
                        # 4. 獲取持倉資訊
                        position_info = trader.get_position()
                        
                        # 5. AI 分析
                        decision = ai_agent.analyze_with_position(
                            market_data=market_data,
                            account_info=account_info,
                            position_info=position_info
                        )
                        
                        # 6. 檢查信心度
                        if decision.get('confidence', 0) >= config['ai_confidence_min']:
                            # 7. 執行交易
                            result = trader.execute_ai_decision(
                                decision=decision,
                                market_data=market_data
                            )
                            
                            with status_placeholder.container():
                                if result['success']:
                                    st.success(f"[OK] {result['action']}: {result['message']}")
                                    st.caption(f"AI 推理: {decision.get('reasoning', 'N/A')[:200]}...")
                                    st.caption(f"風險評估: {decision.get('risk_assessment', 'N/A')}")
                                else:
                                    st.error(f"[ERROR] {result['action']}: {result['message']}")
                        else:
                            with status_placeholder.container():
                                st.warning(f"[SKIP] AI 信心度 {decision.get('confidence', 0)}% < {config['ai_confidence_min']}%，不操作")
                    
                    # 8. 顯示帳戶資訊
                    with info_placeholder.container():
                        render_account_info(trader)
                    
                    # 9. 顯示交易歷史
                    with trades_placeholder.container():
                        render_trade_history(trader)
                
                except Exception as e:
                    with status_placeholder.container():
                        st.error(f"[ERROR] 執行失敗: {e}")
                        st.code(traceback.format_exc())
            
            else:
                # 顯示倒數計時
                remaining = config['update_interval'] - elapsed_minutes
                with status_placeholder.container():
                    st.info(f"[WAITING] 下次更新剩餘: {remaining:.1f} 分鐘")
                
                # 顯示當前資訊
                with info_placeholder.container():
                    render_account_info(trader)
                
                with trades_placeholder.container():
                    render_trade_history(trader)
            
            # 每 5 秒刷新一次
            time.sleep(5)
    
    # === 停止狀態 ===
    elif 'bybit_trader' in st.session_state:
        st.info("[PAUSED] 自動交易已停止")
        
        trader = st.session_state['bybit_trader']
        render_account_info(trader)
        render_trade_history(trader)


def render_account_info(trader: BybitDemoTrader):
    """顯示帳戶資訊"""
    summary = trader.get_account_summary()
    
    st.markdown(f"### [ACCOUNT] 帳戶資訊 - {summary['mode']}")
    
    balance = summary['balance']
    position = summary['position']
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric(
        "總資產",
        f"${balance['total_equity']:,.2f}"
    )
    
    col2.metric(
        "可用餘額",
        f"${balance['available_balance']:,.2f}"
    )
    
    col3.metric(
        "未實現盈虧",
        f"${balance['unrealized_pnl']:,.2f}",
        delta=f"{balance['unrealized_pnl']:+.2f}"
    )
    
    col4.metric(
        "當前槓框",
        f"{summary.get('current_leverage', 1)}x"
    )
    
    if position:
        col5.metric(
            "持倉",
            f"{position['side']} {position['size']:.3f}",
            delta=f"{position['unrealized_pnl']:+.2f} USDT"
        )
    else:
        col5.metric("持倉", "無")
    
    # 持倉詳情
    if position:
        with st.expander("[POSITION] 持倉詳情"):
            st.json(position)


def render_trade_history(trader: BybitDemoTrader):
    """顯示交易歷史"""
    st.markdown("### [HISTORY] 交易歷史")
    
    df = trader.get_trade_history_df()
    
    if not df.empty:
        st.dataframe(
            df[[
                'time', 'side', 'quantity', 'leverage',
                'stop_loss', 'take_profit', 'order_id'
            ]].tail(20),
            width='stretch'
        )
    else:
        st.info("尚無交易記錄")
