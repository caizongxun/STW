import streamlit as st
from .config import V3Config
from .trainer import V3Trainer
from .backtester import V3Backtester
from .features import V3FeatureEngine
from core.data_loader import DataLoader

def render():
    st.header("V3 - 三重障礙反轉策略 (Optimized)")
    st.info("已應用豆包優化建議：引入SMOTE過採樣、新增高階技術與形態特徵、動態寬容標籤、並放寬進場閾值。")
    
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
        
        st.markdown("### 三重障礙設定")
        # 根據建議，縮小止盈止損乘數，讓標籤更容易觸發 (增加正樣本)
        pt_sl = st.slider("止盈止損乘數 (ATR)", 0.5, 3.0, 1.5, 0.1)
        t_bars = st.slider("時間障礙 (K線數)", 24, 200, 48, 12)
        
        st.markdown("### 模型設定")
        # 降低進場閾值，提升 Recall
        signal_threshold = st.slider("進場概率閾值", 0.5, 0.9, 0.6, 0.05)
        
        train_btn = st.button("開始訓練 V3", type="primary", use_container_width=True)
        
    with col2:
        if train_btn:
            with st.spinner("加載數據與訓練中 (包含SMOTE過採樣，請稍候)..."):
                config = V3Config(
                    symbol=symbol,
                    pt_sl_ratio=[pt_sl, pt_sl],
                    t_events_bars=t_bars,
                    signal_threshold=signal_threshold
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
                    
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    col_b.metric("總交易次數", bt_results['total_trades'])
                    col_c.metric("勝率 (%)", f"{bt_results['win_rate']:.2f}%")
                    
                    st.json(bt_results)
                else:
                    st.error("無法加載數據")