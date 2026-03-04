import streamlit as st
import pandas as pd
from .config import V13Config
from .backtester import V13Backtester
from core.data_loader import DataLoader
from core.llm_agent import DeepSeekTradingAgent
import plotly.graph_objects as go
from datetime import datetime

def render():
    st.header("🤖 V13 - DeepSeek-R1 AI 交易決策系統")
    
    st.info("""
    **V13 核心特色**：
    - 🧠 DeepSeek-R1 14B 本地推理引擎
    - 🎯 Chain-of-Thought 多步驟推理
    - 📚 從歷史成功交易中學習 (Prompt Learning)
    - 📊 實時市場數據分析
    - ⚡ 無 API 費用，完全本地化
    """)
    
    # 左右分割布局
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ V13 設定")
        
        # 幣種選擇
        symbol = st.selectbox(
            "💰 交易對",
            ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'DOGEUSDT', 'XRPUSDT']
        )
        
        # 時間框架選擇
        timeframe = st.selectbox(
            "⏰ 時間框架",
            ['15m', '1h', '4h', '1d'],
            index=0  # 預設 15m
        )
        
        capital = st.number_input("💵 起投本金 (USDT)", 1000, 100000, 10000, 1000)
        simulation_days = st.number_input("📆 回測天數", 7, 90, 30, 7)
        
        ai_confidence_min = st.slider(
            "🎯 AI 最低信心門檻 (%)",
            50, 95, 70, 5,
            help="只有當 AI 信心度高於此值時才會開倉"
        )
        
        st.divider()
        
        # 實時信號分析
        if st.button("🔍 獲取實時 AI 信號", type="secondary"):
            with st.spinner("正在調用 DeepSeek-R1 引擎..."):
                loader = DataLoader()
                df = loader.load_data(symbol, timeframe)
                
                if df is not None and len(df) > 200:
                    latest_data = prepare_market_features(df.iloc[-1], df)
                    
                    agent = DeepSeekTradingAgent()
                    decision = agent.analyze_market(latest_data)
                    
                    st.session_state['latest_signal'] = decision
                    st.session_state['latest_symbol'] = symbol
                    st.session_state['latest_timeframe'] = timeframe
                    st.session_state['latest_price'] = latest_data['close']
        
        st.divider()
        
        # 回測按鈕
        test_btn = st.button("🚀 開始 V13 AI 回測", type="primary")
    
    with col2:
        # 顯示實時信號
        if 'latest_signal' in st.session_state:
            st.subheader(f"📶 實時 AI 信號 - {st.session_state.get('latest_symbol', 'N/A')} ({st.session_state.get('latest_timeframe', 'N/A')})")
            
            signal = st.session_state['latest_signal']
            
            # 信號摘要卡片
            if signal['signal'] == 'LONG':
                st.success(f"📈 **看多信號** - 信心度: {signal.get('confidence', 0)}%")
            elif signal['signal'] == 'SHORT':
                st.error(f"📉 **看空信號** - 信心度: {signal.get('confidence', 0)}%")
            else:
                st.warning(f"⏸️ **觀望信號** - 信心度: {signal.get('confidence', 0)}%")
            
            # 詳細交易計劃
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("進場價", f"${signal['entry_price']:,.2f}")
            col_b.metric("止損價", f"${signal['stop_loss']:,.2f}")
            col_c.metric("止盈價", f"${signal['take_profit']:,.2f}")
            
            col_d, col_e = st.columns(2)
            col_d.metric("盈虧比", f"1:{signal.get('risk_reward_ratio', 0):.2f}")
            col_e.metric("建議倉位", f"{signal.get('position_size_percent', 0)}%")
            
            # AI 推理過程
            with st.expander("🧠 查看 AI 推理過程"):
                st.text_area(
                    "DeepSeek-R1 分析",
                    signal.get('reasoning', 'N/A'),
                    height=200
                )
            
            # 風險提示
            if signal.get('key_risks'):
                with st.expander("⚠️ 關鍵風險提示"):
                    for risk in signal['key_risks']:
                        st.warning(f"• {risk}")
            
            # 等待條件（僅用於 HOLD）
            if signal['signal'] == 'HOLD' and signal.get('wait_conditions'):
                with st.expander("⏳ 建議等待的市場條件"):
                    for cond in signal['wait_conditions']:
                        st.info(f"• {cond}")
        
        # 回測結果
        if test_btn:
            with st.spinner("正在載入數據並啟動 DeepSeek-R1 引擎..."):
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
                        st.success("✅ V13 AI 回測完成！")
                        
                        # 績效指標
                        st.subheader("📊 回測績效")
                        
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
                        st.subheader("🤖 AI 決策分析")
                        
                        col_ai1, col_ai2, col_ai3 = st.columns(3)
                        col_ai1.metric("AI 信號數", results.get('ai_signals_count', 0))
                        col_ai2.metric("AI 平均信心", f"{results.get('ai_avg_confidence', 0):.1f}%")
                        col_ai3.metric("實際開倉率", f"{results.get('execution_rate', 0):.1f}%")
                        
                        # 資金曲線
                        if results.get('equity_curve'):
                            st.subheader("📈 資金曲線")
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
                            st.info(f"📚 本次回測新增 {results['learned_cases']} 個成功案例到 AI 學習庫")
                    else:
                        st.error(f"❌ 回測失敗：{results['error']}")
                else:
                    st.error("❌ 無法載入數據，請檢查幣種與時間框架設定")

def prepare_market_features(row, df):
    """將 DataFrame 的一行轉換為 DeepSeek 需要的格式"""
    import talib
    
    # 計算技術指標
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    
    rsi = talib.RSI(close, timeperiod=14)
    macd, macd_signal, macd_hist = talib.MACD(close)
    bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20)
    ema50 = talib.EMA(close, timeperiod=50)
    ema200 = talib.EMA(close, timeperiod=200)
    atr = talib.ATR(high, low, close, timeperiod=14)
    
    # 當前 K 線的索引
    idx = len(df) - 1
    
    # 布林帶位置（0=下軌, 1=上軌）
    bb_pos = 0.5
    if bb_upper[idx] != bb_lower[idx]:
        bb_pos = (close[idx] - bb_lower[idx]) / (bb_upper[idx] - bb_lower[idx])
    
    # 成交量比率
    vol_ma = pd.Series(volume).rolling(24).mean().values
    vol_ratio = volume[idx] / vol_ma[idx] if vol_ma[idx] > 0 else 1.0
    
    return {
        'symbol': row.get('symbol', 'UNKNOWN'),
        'close': float(row['close']),
        'rsi': float(rsi[idx]) if not pd.isna(rsi[idx]) else 50,
        'macd_hist': float(macd_hist[idx]) if not pd.isna(macd_hist[idx]) else 0,
        'bb_position': float(bb_pos),
        'volume_ratio': float(vol_ratio),
        'ema50': float(ema50[idx]) if not pd.isna(ema50[idx]) else row['close'],
        'ema200': float(ema200[idx]) if not pd.isna(ema200[idx]) else row['close'],
        'atr': float(atr[idx]) if not pd.isna(atr[idx]) else row['close'] * 0.02
    }