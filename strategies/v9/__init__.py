import streamlit as st
from .config import V9Config
from .backtester import V9Backtester
from core.data_loader import DataLoader

def render():
    st.header("V9 - 趨勢回調狙擊手 (多重出場模式)")
    
    st.info("""
    **V9 核心特性**：
    - 🎯 **三種出場模式**：分批止盈 / SMC全額奔跑 / 動態追蹤止盈
    - 📈 **動態超賣過濾**：Z-Score + BB%B + StochRSI
    - 🛡️ **順勢回調**：只在多頭趨勢(EMA200)的回調時進場
    
    **出場模式說明**：
    1. **分批保本 (Partial)**：勝率最高，但盈虧比較低。適合震盪上行。
    2. **全額奔跑 (SMC)**：勝率較低(約35-45%)，但盈虧比極高。適合強單邊趨勢。
    3. **追蹤止盈 (Trailing)**：平衡型。達標後不平倉，只移動止損點保護利潤。
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("V9 設定")
        
        symbol = st.selectbox("交易對", ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
        
        col_cap, col_days = st.columns(2)
        with col_cap:
            capital = st.number_input("起投本金 (U)", 1000, 100000, 10000, 1000)
        with col_days:
            simulation_days = st.number_input("回測天數", 30, 180, 60)
        
        st.markdown("### 出場模式設定 (核心)")
        exit_mode = st.radio(
            "選擇出場邏輯",
            ["trailing", "smc_runner", "partial_tp"],
            format_func=lambda x: {
                "trailing": "🚀 動態追蹤止盈 (推薦)",
                "smc_runner": "💎 SMC 全額奔跑 (高盈虧比)",
                "partial_tp": "🛡️ 分批止盈+保本 (高勝率)"
            }[x]
        )
        
        if exit_mode == "partial_tp":
            tp1_r = st.slider("第一止盈 (R)", 0.5, 2.0, 1.0, 0.1)
            tp2_r = st.slider("第二止盈 (R)", 1.5, 5.0, 2.5, 0.5)
            partial_tp_pct = st.slider("首次止盈平倉比例 (%)", 30, 70, 30, 10) / 100.0
        elif exit_mode == "trailing":
            st.info("當達到啟動點時，止損移至保本；之後價格每上漲 0.5R，止損跟著上移。")
            tp1_r = st.slider("啟動追蹤起點 (R)", 1.0, 2.5, 1.5, 0.1)
            tp2_r = st.slider("極限止盈目標 (R)", 2.0, 10.0, 4.0, 0.5)
            partial_tp_pct = 0.0
        else: # smc_runner
            st.info("不提前平倉，不移動保本，要麼碰到止損，要麼碰到止盈。")
            tp1_r = 0.0
            tp2_r = st.slider("固定止盈目標 (R)", 1.5, 5.0, 2.5, 0.1)
            partial_tp_pct = 0.0
        
        st.markdown("### 風險管理")
        base_risk = st.slider("單筆風險 (%)", 1.0, 5.0, 2.0, 0.5) / 100.0
        max_leverage = st.slider("最大槓桿", 1, 10, 3, 1)
        atr_multiplier = st.slider("止損 ATR 倍數", 0.5, 3.0, 1.5, 0.1)
        
        test_btn = st.button("🚀 開始 V9 回測", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner(f"正在加載 {symbol} 數據..."):
                config = V9Config(
                    symbol=symbol,
                    capital=capital,
                    simulation_days=simulation_days,
                    exit_mode=exit_mode,
                    tp1_r=tp1_r,
                    tp2_r=tp2_r,
                    partial_tp_pct=partial_tp_pct,
                    base_risk=base_risk,
                    max_leverage=max_leverage,
                    atr_multiplier=atr_multiplier
                )
                
                loader = DataLoader()
                df = loader.load_data(symbol, '15m')
                
                if df is not None and not df.empty:
                    st.info(f"📋 正在回測 V9 ({exit_mode} 模式)...")
                    bt = V9Backtester(config)
                    results = bt.run(df)
                    
                    st.success(f"✅ 回測完成！({symbol}) - 測試天數: {results.get('days_tested', 0)} 天")
                    
                    # 資金變化
                    col_a1, col_a2, col_a3 = st.columns(3)
                    col_a1.metric("起始本金", f"{capital:.2f} U")
                    col_a2.metric("最終資金", f"{results['final_capital']:.2f} U",
                                  delta=f"+{(results['final_capital']/capital - 1)*100:.1f}%")
                    profit_usd = results['final_capital'] - capital
                    col_a3.metric("淨利潤", f"{profit_usd:+.2f} U")
                    
                    st.markdown("---")
                    
                    # 績效指標
                    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                    col_b1.metric("總報酬 (%)", f"{results['return_pct']:.2f}%")
                    monthly_return = results['monthly_return']
                    col_b2.metric("月化報酬", f"{monthly_return:.2f}%")
                    col_b3.metric("最大回撤", f"{results['max_drawdown']:.2f}%")
                    col_b4.metric("夏普比率", f"{results.get('sharpe_ratio', 0):.2f}")
                    
                    # 交易統計
                    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                    col_c1.metric("勝率", f"{results['win_rate']:.2f}%")
                    col_c2.metric("總交易", results['total_trades'])
                    col_c3.metric("平均持倉(h)", f"{results.get('avg_holding_hours', 0):.1f}")
                    col_c4.metric("盈虧比", f"{results.get('profit_factor', 0):.2f}")
                    
                    # 出場模式統計
                    st.markdown("---")
                    st.markdown("### 📊 出場分析")
                    stats = results.get('exit_stats', {})
                    
                    col_d1, col_d2, col_d3 = st.columns(3)
                    
                    if exit_mode == "partial_tp":
                        col_d1.metric("觸發 TP1 (保本)", stats.get('tp1_count', 0))
                        col_d2.metric("觸發 TP2 (全勝)", stats.get('tp2_count', 0))
                        col_d3.metric("直接止損 (全敗)", stats.get('sl_count', 0))
                        st.info("💡 提示：如果止損次數 > TP1次數，代表進場點太差；如果保本次數遠大於 TP2次數，代表 TP1 設太近，容易被震盪洗掉。")
                        
                    elif exit_mode == "trailing":
                        col_d1.metric("成功推保本次數", stats.get('trailing_activated', 0))
                        col_d2.metric("追蹤打損 (獲利)", stats.get('trailing_stopped', 0))
                        col_d3.metric("直接止損 (全敗)", stats.get('sl_count', 0))
                        st.info("💡 提示：成功推保本代表你立於不敗之地。追蹤打損次數多是正常的，這代表策略正在努力讓利潤奔跑。")
                        
                    elif exit_mode == "smc_runner":
                        col_d1.metric("完美止盈", stats.get('tp2_count', 0))
                        col_d2.metric("直接止損", stats.get('sl_count', 0))
                        col_d3.metric("勝率", f"{results['win_rate']:.1f}%")
                        st.info("💡 提示：SMC 模式不看重勝率，只看盈虧比。只要盈虧比大於 2.0，勝率 35% 也能賺錢。")
                    
                else:
                    st.error("無法載入數據")