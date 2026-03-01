import streamlit as st
from .config import V4Config
from .backtester import V4Backtester
from .features import V4FeatureEngine
from core.data_loader import DataLoader

def render():
    st.header("V4 - SMC / ICT Fair Value Gap (FVG) 策略")
    st.info("純 SMC 邏輯：不依賴傳統 RSI 或 MACD，而是專注於「市場結構」與「流動性不平衡(FVG)」。精準狙擊機構訂單塊。")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("SMC 策略參數")
        symbol = st.selectbox("交易對 (V4)", ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'DOGEUSDT'])
        timeframe = '15m'
        
        st.markdown("### 訂單塊 (FVG) 設定")
        ema_trend = st.number_input("大級別趨勢過濾 (EMA)", value=200, help="ICT 講求順勢，只在多頭結構下買入看漲 FVG")
        fvg_max_age = st.slider("FVG 有效期 (K線數)", 3, 50, 12, 1, help="缺口產生後，多久之內回踩才有效")
        
        st.markdown("### 狙擊手風控 (Fixed Risk)")
        risk_per_trade = st.slider("單筆止損風險 (Risk %)", 0.5, 5.0, 2.0, 0.5, help="無論止損距離多遠，打止損固定只虧總資金的 N%") / 100.0
        
        st.markdown("### 盈虧比 (R:R)")
        col_rr1, col_rr2 = st.columns(2)
        with col_rr1:
            rr_ratio = st.number_input("目標盈虧比 (R)", value=3.0, step=0.5, help="止盈距離是止損距離的幾倍")
        with col_rr2:
            be_ratio = st.number_input("保本推移 (R)", value=1.5, step=0.1, help="當獲利達到幾倍 R 時，將止損移至成本價")
            
        test_btn = st.button("開始回測 SMC", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner("掃描市場結構與 FVG 中..."):
                config = V4Config(
                    symbol=symbol,
                    ema_trend=ema_trend,
                    fvg_max_age=fvg_max_age,
                    risk_per_trade=risk_per_trade,
                    risk_reward_ratio=rr_ratio,
                    breakeven_r=be_ratio
                )
                
                loader = DataLoader()
                df = loader.load_data(symbol, timeframe)
                
                if df is not None and not df.empty:
                    bt = V4Backtester(config)
                    fe = V4FeatureEngine(config)
                    bt_results = bt.run(df, fe)
                    
                    st.success(f"SMC 回測完成！ ({symbol} {timeframe})")
                    
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    col_b.metric("預估月化報酬", f"{bt_results['monthly_return']:.2f}%")
                    col_c.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                        
                    col_d, col_e, col_f = st.columns(3)
                    col_d.metric("勝率 (%)", f"{bt_results['win_rate']:.2f}%")
                    col_e.metric("總交易次數", bt_results['total_trades'])
                    
                    avg_w = bt_results['avg_win_pct']
                    avg_l = abs(bt_results['avg_loss_pct'])
                    rr_actual = (avg_w / avg_l) if avg_l > 0 else 0
                    col_f.metric("實際盈虧比", f"1 : {rr_actual:.2f}")
                    
                    st.json(bt_results)
                    
                    if bt_results['return_pct'] > 0:
                        st.balloons()
                else:
                    st.error("無法加載數據")