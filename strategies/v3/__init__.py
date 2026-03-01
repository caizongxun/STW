import streamlit as st
from .config import V3Config
from .trainer import V3Trainer
from .backtester import V3Backtester
from .features import V3FeatureEngine
from core.data_loader import DataLoader

def render():
    st.header("V3 - 三重障礙反轉策略 (二次優化版)")
    st.info("解決過度交易問題：引入冷卻期、多因子信號過濾、真實交易成本計算與倉位風險控制。")
    
    tab1, tab2 = st.tabs(["模型訓練", "策略回測"])
    
    with tab1:
        render_training()
        
    with tab2:
        st.info("請先進行訓練，回測結果會在訓練後自動展示。")

def render_training():
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("參數設定")
        symbol = st.selectbox("交易對 (V3)", ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'])
        timeframe = '15m'
        
        st.markdown("### 信號與風控設定")
        # 提高預設閾值過濾假信號
        signal_threshold = st.slider("進場概率閾值", 0.5, 0.9, 0.65, 0.05)
        # 冷卻期
        cooldown = st.slider("交易冷卻期 (K線數)", 0, 20, 5, 1)
        # 倉位控制
        position_pct = st.slider("單筆最大倉位 (%)", 5, 100, 10, 5) / 100.0
        
        train_btn = st.button("開始訓練 V3", type="primary", use_container_width=True)
        
    with col2:
        if train_btn:
            with st.spinner("加載數據與訓練中..."):
                config = V3Config(
                    symbol=symbol,
                    signal_threshold=signal_threshold,
                    cooldown_bars=cooldown,
                    position_pct=position_pct
                )
                
                loader = DataLoader()
                df = loader.load_data(symbol, timeframe)
                
                if df is not None and not df.empty:
                    trainer = V3Trainer(config)
                    results = trainer.train(df)
                    
                    st.success("V3 訓練完成！")
                    st.json(results)
                    
                    st.subheader("樣本外回測 (Out of Sample)")
                    bt = V3Backtester(config)
                    test_df = df.iloc[int(len(df)*0.8):].reset_index(drop=True)
                    bt_results = bt.run(test_df, trainer.long_model, trainer.short_model, V3FeatureEngine(config))
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    col_b.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                    col_c.metric("總交易次數", bt_results['total_trades'])
                    col_d.metric("勝率 (%)", f"{bt_results['win_rate']:.2f}%")
                    
                    if bt_results['return_pct'] < 0:
                        st.warning("策略仍處於虧損狀態，請嘗試調整「進場概率閾值」或增加「交易冷卻期」。")
                    elif bt_results['total_trades'] < 10:
                        st.info("交易次數偏少，策略偏向保守。")
                    else:
                        st.balloons()
                else:
                    st.error("無法加載數據")