import streamlit as st
import pandas as pd
from .config import V13Config
from .backtester import V13Backtester
from .case_manager import render_case_manager
from .auto_trader import render_auto_trader_ui
from .bybit_demo_tab import render_bybit_demo_tab
from core.data_loader import DataLoader
from core.llm_agent_enhanced import EnhancedDeepSeekAgent
import plotly.graph_objects as go
from datetime import datetime
import traceback

def render():
    st.header("[V13] DeepSeek-R1 AI 交易決策系統")
    
    st.info("""
    **V13 核心特色**：
    - DeepSeek-R1 14B 本地推理引擎
    - Chain-of-Thought 多步驟推理
    - 從歷史成功交易中學習 (40+ 技術指標)
    - 整合新聞情緒分析 (CryptoPanic API)
    - 每 15 分鐘自動更新訊號
    - Bybit Demo 模擬交易 (新功能)
    - 無 API 費用，完全本地化
    """)
    
    # 主頁籤
    main_tab1, main_tab2, main_tab3, main_tab4, main_tab5 = st.tabs([
        "[SIGNAL] 實時訊號 & 回測", 
        "[AUTO] 自動更新", 
        "[BYBIT] Demo 交易",
        "[CASES] 學習案例庫", 
        "[CONFIG] 設定"
    ])
    
    # === Tab 1: 實時訊號 & 回測 ===
    with main_tab1:
        render_trading_interface()
    
    # === Tab 2: 自動更新 ===
    with main_tab2:
        render_auto_trader_ui()
    
    # === Tab 3: Bybit Demo 交易 ===
    with main_tab3:
        render_bybit_demo_tab()
    
    # === Tab 4: 學習案例庫 ===
    with main_tab4:
        render_case_manager()
    
    # === Tab 5: 設定 ===
    with main_tab5:
        render_settings()


def render_trading_interface():
    """渲染交易界面（原本的V13功能）"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("[SETUP] V13 設定")
        
        # 幣種選擇
        symbol = st.selectbox(
            "[SYMBOL] 交易對",
            ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'DOGEUSDT', 'XRPUSDT']
        )
        
        # 時間框架選擇
        timeframe = st.selectbox(
            "[TIMEFRAME] 時間框架",
            ['15m', '1h', '4h', '1d'],
            index=0
        )
        
        capital = st.number_input("[CAPITAL] 起投本金 (USDT)", 1000, 100000, 10000, 1000)
        simulation_days = st.number_input("[DAYS] 回測天數", 7, 90, 30, 7)
        
        ai_confidence_min = st.slider(
            "[CONFIDENCE] AI 最低信心門檻 (%)",
            50, 95, 70, 5,
            help="只有當 AI 信心度高於此值時才會開倉"
        )
        
        use_enhanced = st.checkbox(
            "[ENHANCED] 使用強化AI引擎（注入40+指標）",
            value=True,
            help="強化版會自動匹配相似案例並注入到Prompt"
        )
        
        enable_news = st.checkbox(
            "[NEWS] 啟用新聞分析",
            value=True,
            help="整合 CryptoPanic API 的新聞情緒分析"
        )
        
        st.divider()
        
        # 實時訊號分析
        if st.button("[ANALYZE] 獲取實時 AI 訊號", type="secondary"):
            with st.spinner("正在調用 DeepSeek-R1 引擎...預計 10-20 秒"):
                try:
                    loader = DataLoader()
                    df = loader.load_data(symbol, timeframe)
                    
                    if df is not None and len(df) > 200:
                        latest_data = prepare_market_features(df.iloc[-1], df)
                        
                        if use_enhanced:
                            agent = EnhancedDeepSeekAgent()
                        else:
                            from core.llm_agent import DeepSeekTradingAgent
                            agent = DeepSeekTradingAgent()
                        
                        decision = agent.analyze_market(latest_data)
                        
                        # 新聞分析
                        news_summary = None
                        if enable_news:
                            from core.news_fetcher import CryptoNewsFetcher
                            news_fetcher = CryptoNewsFetcher()
                            news_symbol = symbol.replace('USDT', '')
                            news_context = news_fetcher.get_news_context_for_trading(news_symbol)
                            
                            if news_context['has_news']:
                                news_summary = f"{news_context['sentiment'].upper()} ({news_context['news_count']} news)\n{news_context['recommendation']}"
                                decision['news_context'] = news_context
                        
                        st.session_state['latest_signal'] = decision
                        st.session_state['latest_symbol'] = symbol
                        st.session_state['latest_timeframe'] = timeframe
                        st.session_state['latest_price'] = latest_data['close']
                        st.session_state['news_summary'] = news_summary
                        st.success("[OK] AI 分析完成！")
                    else:
                        st.error("[ERROR] 數據不足，至少需要 200 根 K 線")
                except Exception as e:
                    st.error(f"[ERROR] 分析失敗：{str(e)}")
                    st.code(traceback.format_exc())
        
        st.divider()
        
        # 回測按鈕
        test_btn = st.button("[BACKTEST] 開始 V13 AI 回測", type="primary")
    
    with col2:
        # 顯示實時訊號
        if 'latest_signal' in st.session_state:
            st.subheader(f"[SIGNAL] 實時 AI 訊號 - {st.session_state.get('latest_symbol', 'N/A')} ({st.session_state.get('latest_timeframe', 'N/A')})")
            
            signal = st.session_state['latest_signal']
            
            # 檢查是否有錯誤
            if 'error' in signal:
                st.error(f"[ERROR] AI 分析出錯：{signal['error']}")
                if 'parse_error' in signal:
                    st.warning("[INFO] JSON 解析失敗，這可能是 DeepSeek 輸出格式問題。請再試一次。")
                with st.expander("[DEBUG] 查看原始輸出"):
                    st.text(signal.get('reasoning', 'N/A'))
            else:
                # 訊號摘要卡片
                if signal['signal'] == 'LONG':
                    st.success(f"[LONG] **看多訊號** - 信心度: {signal.get('confidence', 0)}%")
                elif signal['signal'] == 'SHORT':
                    st.error(f"[SHORT] **看空訊號** - 信心度: {signal.get('confidence', 0)}%")
                else:
                    st.warning(f"[HOLD] **觀望訊號** - 信心度: {signal.get('confidence', 0)}%")
                
                # 詳細交易計劃
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("進場價", f"${signal['entry_price']:,.2f}")
                col_b.metric("止損價", f"${signal['stop_loss']:,.2f}")
                col_c.metric("止盈價", f"${signal['take_profit']:,.2f}")
                
                col_d, col_e = st.columns(2)
                risk_reward = (signal['take_profit'] - signal['entry_price']) / (signal['entry_price'] - signal['stop_loss']) if signal['entry_price'] != signal['stop_loss'] else 0
                col_d.metric("盈虧比", f"1:{risk_reward:.2f}")
                col_e.metric("建議倉位", f"{signal.get('position_size_percent', 0)}%")
                
                # 新聞摘要
                if st.session_state.get('news_summary'):
                    st.info(f"[NEWS] **新聞情緒**\n{st.session_state['news_summary']}")
                
                # 匹配案例（強化版獨有）
                if signal.get('matched_cases'):
                    with st.expander(f"[CASES] 匹配到 {len(signal['matched_cases'])} 個相似案例"):
                        for case_id in signal['matched_cases']:
                            st.caption(f"- {case_id}")
                
                # AI 推理過程
                with st.expander("[REASONING] 查看 AI 推理過程"):
                    st.text_area(
                        "DeepSeek-R1 分析",
                        signal.get('reasoning', 'N/A'),
                        height=200
                    )
                
                # 風險提示
                if signal.get('key_risks'):
                    with st.expander("[RISKS] 關鍵風險提示"):
                        for risk in signal['key_risks']:
                            st.warning(f"- {risk}")
        
        # 回測結果
        if test_btn:
            with st.spinner("正在載入數據並啟動 DeepSeek-R1 引擎..."):
                try:
                    config = V13Config(
                        symbol=symbol,
                        timeframe=timeframe,
                        capital=capital,
                        simulation_days=simulation_days,
                        ai_confidence_threshold=ai_confidence_min / 100.0
                    )
                    
                    loader = DataLoader()
                    df = loader.load_data(symbol, timeframe)
                    
                    if df is not None and not df.empty:
                        bt = V13Backtester(config)
                        results = bt.run(df)
                        
                        if 'error' not in results:
                            st.success("[OK] V13 AI 回測完成！")
                            
                            # 績效指標
                            st.subheader("[PERFORMANCE] 回測績效")
                            
                            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                            col_r1.metric("總報酬", f"{results['return_pct']:.2f}%")
                            col_r2.metric("月報酬", f"{results['monthly_return']:.2f}%")
                            col_r3.metric("勝率", f"{results['win_rate']:.1f}%")
                            col_r4.metric("總交易", results['total_trades'])
                            
                            col_r5, col_r6, col_r7, col_r8 = st.columns(4)
                            col_r5.metric("最大回撤", f"{results['max_drawdown']:.2f}%")
                            col_r6.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
                            col_r7.metric("盈虧比", f"{results['profit_factor']:.2f}")
                            col_r8.metric("平均持倉", f"{results['avg_holding_hours']:.1f}h")
                            
                            # AI 決策統計
                            st.subheader("[AI] AI 決策分析")
                            
                            col_ai1, col_ai2, col_ai3 = st.columns(3)
                            col_ai1.metric("AI 訊號數", results.get('ai_signals_count', 0))
                            col_ai2.metric("AI 平均信心", f"{results.get('ai_avg_confidence', 0):.1f}%")
                            col_ai3.metric("實際開倉率", f"{results.get('execution_rate', 0):.1f}%")
                            
                            # 資金曲線
                            if results.get('equity_curve'):
                                st.subheader("[EQUITY] 資金曲線")
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    y=results['equity_curve'],
                                    mode='lines',
                                    name='資金',
                                    line=dict(color='#00d4ff', width=2)
                                ))
                                fig.update_layout(
                                    height=300,
                                    margin=dict(l=0, r=0, t=30, b=0),
                                    hovermode='x unified'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # 成功案例學習狀況
                            if results.get('learned_cases', 0) > 0:
                                st.info(f"[LEARNED] 本次回測新增 {results['learned_cases']} 個成功案例到 AI 學習庫")
                        else:
                            st.error(f"[ERROR] 回測失敗：{results['error']}")
                            st.code(traceback.format_exc())
                    else:
                        st.error("[ERROR] 無法載入數據，請檢查幣種與時間框架設定")
                except Exception as e:
                    st.error(f"[ERROR] 系統錯誤：{str(e)}")
                    st.code(traceback.format_exc())


def render_settings():
    """渲染設定頁面"""
    st.subheader("[CONFIG] V13 進階設定")
    
    st.markdown("""
    ### [OLLAMA] Ollama 配置
    
    **前提條件**：
    1. 已安裝 Ollama：`ollama -v`
    2. 已下載 DeepSeek-R1 14B：`ollama pull deepseek-r1:14b`
    3. Ollama 服務正在運行：`curl http://localhost:11434`
    
    **性能調整**：
    - 推理速度：約 2-3 tokens/秒（RTX 3060）
    - 離線運行：不需網路連接
    - 資源占用：VRAM ~8GB + RAM ~4GB
    """)
    
    st.divider()
    
    st.markdown("""
    ### [BYBIT] Bybit Testnet 設定
    
    **申請步驟**：
    1. 前往 [testnet.bybit.com](https://testnet.bybit.com)
    2. 註冊/登入帳戶
    3. 進入 API Management 創建 API Key
    4. 領取免費模擬資金 (100,000 USDT)
    
    **注意事項**：
    - Testnet 資金無法提現，僅供測試
    - 使用真實市場數據，但不會影響真實帳戶
    - 建議先在 Testnet 測試 1-2 週，確認策略有效再上真實盤
    """)
    
    st.divider()
    
    st.markdown("""
    ### [NEWS] 新聞 API 配置
    
    **CryptoPanic API**：
    - 免費版本：每小時 300 請求
    - 申請地址：[https://cryptopanic.com/developers/api/](https://cryptopanic.com/developers/api/)
    - 使用方式：無需 token 也可使用（但限制較多）
    
    **功能**：
    - 自動獲取最近 24 小時新聞
    - 情緒分析（看多/看空/中性）
    - 信心度調整（增加/減少 AI 信心度）
    """)
    
    st.divider()
    
    st.markdown("""
    ### [CASES] 學習案例管理
    
    **建議數量**：
    - 最少：20-30 個案例（防止過擬合）
    - 理想：50-100 個案例（涵蓋多種市場狀況）
    - 最大：200 個案例（Prompt 長度限制）
    
    **品質控制**：
    - 多空平衡：LONG:SHORT ≈ 1:1
    - 獲利多樣：包含 1-5% 的各種獲利
    - 持倉時間：短線/中線/長線都要有
    - 時間分布：不同時間段的成功案例
    """)
    
    st.divider()
    
    st.markdown("""
    ### [UPDATES] 更新記錄
    
    **v2.2 (2026-03-05)**
    - 新增 Bybit Demo 自動交易功能
    - 支援模擬資金 + 真實市場
    - 自動止損止盈設置
    
    **v2.1 (2026-03-05)**
    - 新增 15 分鐘自動更新功能
    - 整合 CryptoPanic 新聞 API
    - 修復 null 解析問題
    - 新增 V2 強化引擎 (llm_agent_v2)
    
    **v2.0 (2026-03-04)**
    - 新增強化AI引擎（`EnhancedDeepSeekAgent`）
    - 支援40+技術指標完整特徵提取
    - 自動案例相似度匹配
    - 視覺化案例管理界面
    - 批量導入歷史獲利案例
    
    **v1.0 (2026-03-01)**
    - 基礎 DeepSeek-R1 整合
    - 簡化版 Prompt Learning
    - 回測引擎
    """)


def prepare_market_features(row, df):
    """將 DataFrame 的一行轉換為 DeepSeek 需要的格式（強化版：40+指標）"""
    import talib
    
    # 計算技術指標
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    
    # 趋勢
    ema9 = talib.EMA(close, timeperiod=9)
    ema21 = talib.EMA(close, timeperiod=21)
    ema50 = talib.EMA(close, timeperiod=50)
    ema200 = talib.EMA(close, timeperiod=200)
    macd, macd_signal, macd_hist = talib.MACD(close)
    adx = talib.ADX(high, low, close, timeperiod=14)
    
    # 動能
    rsi = talib.RSI(close, timeperiod=14)
    stoch_k, stoch_d = talib.STOCH(high, low, close)
    cci = talib.CCI(high, low, close, timeperiod=14)
    mfi = talib.MFI(high, low, close, volume, timeperiod=14)
    willr = talib.WILLR(high, low, close, timeperiod=14)
    
    # 波動
    atr = talib.ATR(high, low, close, timeperiod=14)
    bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20)
    
    # 成交量
    volume_ma = pd.Series(volume).rolling(20).mean().values
    obv = talib.OBV(close, volume)
    
    idx = len(df) - 1
    
    # 布林帶位置
    bb_pos = 0.5
    if bb_upper[idx] != bb_lower[idx]:
        bb_pos = (close[idx] - bb_lower[idx]) / (bb_upper[idx] - bb_lower[idx])
    
    # 成交量比率
    vol_ratio = volume[idx] / volume_ma[idx] if volume_ma[idx] > 0 else 1.0
    
    # 支撐/壓力
    pivot = (high[idx] + low[idx] + close[idx]) / 3
    resistance = pivot + (high[idx] - low[idx])
    support = pivot - (high[idx] - low[idx])
    
    return {
        'symbol': row.get('symbol', 'UNKNOWN'),
        'close': float(row['close']),
        
        # 趋勢
        'ema9': float(ema9[idx]) if not pd.isna(ema9[idx]) else row['close'],
        'ema21': float(ema21[idx]) if not pd.isna(ema21[idx]) else row['close'],
        'ema50': float(ema50[idx]) if not pd.isna(ema50[idx]) else row['close'],
        'ema200': float(ema200[idx]) if not pd.isna(ema200[idx]) else row['close'],
        'macd': float(macd[idx]) if not pd.isna(macd[idx]) else 0,
        'macd_signal': float(macd_signal[idx]) if not pd.isna(macd_signal[idx]) else 0,
        'macd_hist': float(macd_hist[idx]) if not pd.isna(macd_hist[idx]) else 0,
        'adx': float(adx[idx]) if not pd.isna(adx[idx]) else 0,
        
        # 動能
        'rsi': float(rsi[idx]) if not pd.isna(rsi[idx]) else 50,
        'stoch_k': float(stoch_k[idx]) if not pd.isna(stoch_k[idx]) else 50,
        'stoch_d': float(stoch_d[idx]) if not pd.isna(stoch_d[idx]) else 50,
        'cci': float(cci[idx]) if not pd.isna(cci[idx]) else 0,
        'mfi': float(mfi[idx]) if not pd.isna(mfi[idx]) else 50,
        'willr': float(willr[idx]) if not pd.isna(willr[idx]) else -50,
        
        # 波動
        'atr': float(atr[idx]) if not pd.isna(atr[idx]) else row['close'] * 0.02,
        'bb_upper': float(bb_upper[idx]) if not pd.isna(bb_upper[idx]) else row['close'] * 1.02,
        'bb_middle': float(bb_middle[idx]) if not pd.isna(bb_middle[idx]) else row['close'],
        'bb_lower': float(bb_lower[idx]) if not pd.isna(bb_lower[idx]) else row['close'] * 0.98,
        'bb_position': float(bb_pos),
        
        # 成交量
        'volume_ratio': float(vol_ratio),
        'obv': float(obv[idx]) if not pd.isna(obv[idx]) else 0,
        
        # 支撐/壓力
        'dist_to_resistance': float((resistance - close[idx]) / close[idx] * 100),
        'dist_to_support': float((close[idx] - support) / close[idx] * 100)
    }