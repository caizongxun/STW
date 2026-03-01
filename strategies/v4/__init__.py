import streamlit as st
from .config import V4Config
from .backtester import V4Backtester
from .features import V4FeatureEngine
from core.data_loader import DataLoader

def render():
    st.header("V4 - 純指標順勢回踩策略 (Pure Indicator / No ML)")
    st.info("暫時放棄 AI 模型預測。使用經典的 SMC (Smart Money Concept) / 均線回踩邏輯，結合 K 線形態與動態風控進行純回測。")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("策略參數設定")
        symbol = st.selectbox("交易對 (V4)", ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'DOGEUSDT'])
        timeframe = '15m'
        
        st.markdown("### 趨勢與進場")
        ema_fast = st.number_input("快線 EMA", value=50)
        ema_slow = st.number_input("慢線 EMA", value=200)
        
        col_rsi1, col_rsi2 = st.columns(2)
        with col_rsi1:
            rsi_oversold = st.number_input("RSI 超賣 (多頭回調)", value=35)
        with col_rsi2:
            rsi_overbought = st.number_input("RSI 超買 (空頭反彈)", value=65)
            
        use_pa = st.checkbox("強制要求 K線反轉形態 (下/上影線)", value=True)
        
        st.markdown("### 風控與盈虧比 (核心)")
        risk_per_trade = st.slider("單筆風險 (Risk %)", 1.0, 10.0, 3.0, 0.5) / 100.0
        
        col_sl, col_tp = st.columns(2)
        with col_sl:
            atr_sl = st.slider("止損乘數 (ATR)", 0.5, 3.0, 1.5, 0.1)
        with col_tp:
            atr_tp = st.slider("止盈乘數 (ATR)", 1.0, 8.0, 4.0, 0.5)
            
        test_btn = st.button("開始回測 V4", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner("載入資料並執行策略回測中..."):
                config = V4Config(
                    symbol=symbol,
                    ema_fast=ema_fast,
                    ema_slow=ema_slow,
                    rsi_oversold=rsi_oversold,
                    rsi_overbought=rsi_overbought,
                    use_price_action=use_pa,
                    risk_per_trade=risk_per_trade,
                    atr_sl_multiplier=atr_sl,
                    atr_tp_multiplier=atr_tp
                )
                
                loader = DataLoader()
                # 因為不訓練模型，我們可以直接使用全部資料來回測
                df = loader.load_data(symbol, timeframe)
                
                if df is not None and not df.empty:
                    bt = V4Backtester(config)
                    fe = V4FeatureEngine(config)
                    bt_results = bt.run(df, fe)
                    
                    st.success(f"V4 回測完成！ ({symbol} {timeframe})")
                    
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    col_b.metric("預估月化報酬", f"{bt_results['monthly_return']:.2f}%")
                    col_c.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                        
                    col_d, col_e, col_f = st.columns(3)
                    col_d.metric("勝率 (%)", f"{bt_results['win_rate']:.2f}%")
                    col_e.metric("總交易次數", bt_results['total_trades'])
                    
                    # 顯示實際盈虧比
                    avg_w = bt_results['avg_win_pct']
                    avg_l = abs(bt_results['avg_loss_pct'])
                    rr_ratio = (avg_w / avg_l) if avg_l > 0 else 0
                    col_f.metric("實際盈虧比", f"1 : {rr_ratio:.2f}")
                    
                    st.json(bt_results)
                else:
                    st.error("無法加載數據")