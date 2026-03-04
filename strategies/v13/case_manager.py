"""
V13 案例管理器 GUI
視覺化管理成功交易案例，支援查看/編輯/刪除/批量導入
"""
import streamlit as st
import pandas as pd
import json
from pathlib import Path
from core.case_extractor import CaseExtractor
from core.data_loader import DataLoader
import plotly.graph_objects as go
from datetime import datetime


def render_case_manager():
    """渲染案例管理器界面"""
    st.subheader("📚 獲利案例學習庫")
    
    st.info("""
    **功能說明**：
    - 自動從歷史數據中提取獲利 > 1% 的交易
    - 完整保留進場前5根K棒的40+技術指標
    - DeepSeek AI會自動學習這些案例並應用到未來決策
    """)
    
    cases_path = Path("data/detailed_success_cases.json")
    
    # Tab分頁
    tab1, tab2, tab3 = st.tabs(["📋 案例列表", "➕ 批量導入", "📈 統計分析"])
    
    # === Tab 1: 案例列表 ===
    with tab1:
        if not cases_path.exists():
            st.warning("📁 尚無學習案例，請至「批量導入」頁面提取歷史數據")
        else:
            cases_data = load_cases(cases_path)
            
            if cases_data['total_cases'] == 0:
                st.warning("📁 案例庫為空")
            else:
                st.success(f"✅ 已載入 {cases_data['total_cases']} 個案例（特徵數：{cases_data['feature_count']}）")
                st.caption(f"最後更新：{cases_data.get('last_updated', 'N/A')}")
                
                # 篩選器
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    filter_direction = st.multiselect(
                        "方向篩選",
                        ['LONG', 'SHORT'],
                        default=['LONG', 'SHORT']
                    )
                with col_f2:
                    filter_min_profit = st.number_input(
                        "最低獲利%",
                        0.0, 10.0, 1.0, 0.5
                    )
                with col_f3:
                    sort_by = st.selectbox(
                        "排序方式",
                        ["獲利率降序", "時間降序", "持倉時間降序"]
                    )
                
                # 篩選案例
                filtered_cases = []
                for case in cases_data['cases']:
                    if case['direction'] not in filter_direction:
                        continue
                    
                    profit = float(case['outcome'].replace('profit_', '').replace('%', ''))
                    if profit < filter_min_profit:
                        continue
                    
                    filtered_cases.append(case)
                
                # 排序
                if sort_by == "獲利率降序":
                    filtered_cases.sort(
                        key=lambda x: float(x['outcome'].replace('profit_', '').replace('%', '')),
                        reverse=True
                    )
                elif sort_by == "時間降序":
                    filtered_cases.sort(key=lambda x: x['entry_time'], reverse=True)
                elif sort_by == "持倉時間降序":
                    filtered_cases.sort(key=lambda x: x['holding_bars'], reverse=True)
                
                st.divider()
                st.caption(f"🔍 顯示 {len(filtered_cases)} / {cases_data['total_cases']} 個案例")
                
                # 卡片式顯示
                for idx, case in enumerate(filtered_cases):
                    with st.expander(
                        f"{idx+1}. {case['symbol']} {case['direction']} - {case['outcome']} | {case['entry_time']}",
                        expanded=(idx == 0)
                    ):
                        render_case_detail(case)
                        
                        # 刪除按鈕
                        if st.button(f"🗑️ 刪除此案例", key=f"delete_{case['trade_id']}"):
                            delete_case(cases_path, case['trade_id'])
                            st.rerun()
    
    # === Tab 2: 批量導入 ===
    with tab2:
        st.subheader("📥 從歷史數據自動提取獲利案例")
        
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            import_symbol = st.selectbox(
                "💰 選擇幣種",
                ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
            )
            import_timeframe = st.selectbox(
                "⏰ 時間框架",
                ['15m', '1h', '4h'],
                index=1
            )
        
        with col_i2:
            import_days = st.number_input(
                "📆 歷史天數",
                30, 365, 90, 30
            )
            min_profit_pct = st.number_input(
                "🎯 最低獲利%",
                0.5, 5.0, 1.0, 0.5
            )
        
        st.info("""
        **提取邏輯**：
        1. 從 Binance 載入歷史K線數據
        2. 計算40+技術指標
        3. 識別潛在交易訊號（基於RSI超買/超賣 + 成交量爆發）
        4. 模擬交易並篩選獲利 > {min_profit_pct}% 的案例
        5. 提取進場時刻完整特徵並儲存
        """)
        
        if st.button("🚀 開始提取", type="primary"):
            with st.spinner(f"正在載入 {import_symbol} {import_timeframe} 過去 {import_days} 天數據..."):
                try:
                    # 載入數據
                    loader = DataLoader()
                    df = loader.load_data(import_symbol, import_timeframe, days=import_days)
                    
                    if df is None or len(df) < 200:
                        st.error("❌ 數據不足，至少需要200根K線")
                        return
                    
                    st.success(f"✅ 已載入 {len(df)} 根K線")
                    
                    # 模擬交易找到獲利案例
                    with st.spinner("🤖 正在識別獲利交易訊號..."):
                        trades = simulate_trades(df, import_symbol, min_profit_pct)
                    
                    if not trades:
                        st.warning(f"⚠️ 未找到獲利 > {min_profit_pct}% 的交易，嘗試：\n- 降低最低獲利%\n- 增加歷史天數")
                        return
                    
                    st.success(f"✅ 識別到 {len(trades)} 筆獲利交易")
                    
                    # 提取案例
                    with st.spinner("🔍 正在提取40+技術指標特徵..."):
                        extractor = CaseExtractor()
                        cases = extractor.extract_from_trades(df, trades)
                    
                    if cases:
                        new_count = extractor.save_cases(cases, str(cases_path))
                        st.success(f"🎉 成功新增 {new_count} 個案例到學習庫！")
                        st.balloons()
                    else:
                        st.warning("⚠️ 未能提取有效案例")
                
                except Exception as e:
                    st.error(f"❌ 提取失敗：{str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # === Tab 3: 統計分析 ===
    with tab3:
        if not cases_path.exists():
            st.warning("📁 尚無案例數據")
        else:
            cases_data = load_cases(cases_path)
            render_statistics(cases_data)


def render_case_detail(case: dict):
    """渲染單個案例的詳細資訊"""
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    col_d1.metric("💵 進場價", f"${case['entry_price']:,.2f}")
    col_d2.metric("💰 出場價", f"${case['exit_price']:,.2f}")
    col_d3.metric("⏱️ 持倉", f"{case['holding_bars']} bars")
    col_d4.metric("🎯 獲利", case['outcome'])
    
    st.markdown(f"**🧠 進場邏輯**：{case.get('entry_logic', 'N/A')}")
    
    # 指標趨勢
    if case.get('indicator_trends'):
        st.markdown("**📈 關鍵指標趨勢**：")
        
        for indicator, trend_data in case['indicator_trends'].items():
            values = trend_data['values']
            trend = trend_data['trend']
            
            trend_emoji = "📈" if trend == 'rising' else "📉" if trend == 'falling' else "➡️"
            values_str = " → ".join([f"{v:.2f}" for v in values])
            
            st.caption(f"{trend_emoji} **{indicator}**: {values_str}")
    
    # 進場時刻指標快照
    entry_candle = next((c for c in case['candles'] if c['position'] == 'entry'), None)
    if entry_candle:
        with st.expander("🔍 查看進場時刻完整指標"):
            indicators_df = pd.DataFrame([entry_candle['indicators']]).T
            indicators_df.columns = ['數值']
            st.dataframe(indicators_df, use_container_width=True)


def load_cases(filepath: Path) -> dict:
    """載入案例數據"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def delete_case(filepath: Path, trade_id: str):
    """刪除指定案例"""
    data = load_cases(filepath)
    data['cases'] = [c for c in data['cases'] if c['trade_id'] != trade_id]
    data['total_cases'] = len(data['cases'])
    data['last_updated'] = pd.Timestamp.now().isoformat()
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    st.success(f"✅ 已刪除案例: {trade_id}")


def simulate_trades(df: pd.DataFrame, symbol: str, min_profit_pct: float) -> list:
    """
    模擬簡單的RSI超買/超賣策略，找到獲利交易
    這只是示範，實際應使用你的V13回測引擎的交易記錄
    """
    import talib
    
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    
    rsi = talib.RSI(close, timeperiod=14)
    volume_ma = pd.Series(volume).rolling(20).mean().values
    
    trades = []
    position = None
    
    for i in range(100, len(df) - 20):  # 保留前100根計算指標，後20根看結果
        if position is None:
            # LONG條件：RSI<30 + 成交量>1.5x
            if rsi[i] < 30 and volume[i] > volume_ma[i] * 1.5:
                position = {
                    'direction': 'LONG',
                    'entry_idx': i,
                    'entry_time': str(df.iloc[i]['timestamp'] if 'timestamp' in df.columns else df.index[i]),
                    'entry_price': close[i]
                }
            # SHORT條件：RSI>70 + 成交量>1.5x
            elif rsi[i] > 70 and volume[i] > volume_ma[i] * 1.5:
                position = {
                    'direction': 'SHORT',
                    'entry_idx': i,
                    'entry_time': str(df.iloc[i]['timestamp'] if 'timestamp' in df.columns else df.index[i]),
                    'entry_price': close[i]
                }
        else:
            # 檢查是否獲利
            if position['direction'] == 'LONG':
                pnl_pct = (close[i] - position['entry_price']) / position['entry_price'] * 100
                if pnl_pct >= min_profit_pct or pnl_pct <= -2.0:  # 止盈或止損
                    if pnl_pct >= min_profit_pct:
                        trades.append({
                            'symbol': symbol,
                            'direction': position['direction'],
                            'entry_time': position['entry_time'],
                            'exit_time': str(df.iloc[i]['timestamp'] if 'timestamp' in df.columns else df.index[i]),
                            'entry_price': position['entry_price'],
                            'exit_price': close[i],
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'TP' if pnl_pct > 0 else 'SL'
                        })
                    position = None
            else:  # SHORT
                pnl_pct = (position['entry_price'] - close[i]) / position['entry_price'] * 100
                if pnl_pct >= min_profit_pct or pnl_pct <= -2.0:
                    if pnl_pct >= min_profit_pct:
                        trades.append({
                            'symbol': symbol,
                            'direction': position['direction'],
                            'entry_time': position['entry_time'],
                            'exit_time': str(df.iloc[i]['timestamp'] if 'timestamp' in df.columns else df.index[i]),
                            'entry_price': position['entry_price'],
                            'exit_price': close[i],
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'TP' if pnl_pct > 0 else 'SL'
                        })
                    position = None
    
    return trades


def render_statistics(cases_data: dict):
    """渲染案例統計分析"""
    cases = cases_data['cases']
    
    if not cases:
        st.warning("📁 無案例數據")
        return
    
    # 基礎統計
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    
    long_count = sum(1 for c in cases if c['direction'] == 'LONG')
    short_count = sum(1 for c in cases if c['direction'] == 'SHORT')
    
    profits = [float(c['outcome'].replace('profit_', '').replace('%', '')) for c in cases]
    avg_profit = sum(profits) / len(profits)
    max_profit = max(profits)
    
    avg_holding = sum(c['holding_bars'] for c in cases) / len(cases)
    
    col_s1.metric("📈 總案例數", len(cases))
    col_s2.metric("🔴 LONG / 🔵 SHORT", f"{long_count} / {short_count}")
    col_s3.metric("🎯 平均獲利", f"{avg_profit:.2f}%")
    col_s4.metric("⏱️ 平均持倉", f"{avg_holding:.1f} bars")
    
    # 獲利分佈圖
    st.subheader("📊 獲利率分佈")
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=profits,
        nbinsx=20,
        marker_color='#00d4ff'
    ))
    fig.update_layout(
        xaxis_title="獲利率 (%)",
        yaxis_title="次數",
        height=300,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top 10 最佳案例
    st.subheader("🏆 Top 10 最佳獲利案例")
    top_cases = sorted(cases, key=lambda x: float(x['outcome'].replace('profit_', '').replace('%', '')), reverse=True)[:10]
    
    top_df = pd.DataFrame([{
        '排名': idx + 1,
        '幣種': c['symbol'],
        '方向': c['direction'],
        '獲利': c['outcome'],
        '進場時間': c['entry_time'],
        '持倉': f"{c['holding_bars']} bars",
        '進場邏輯': c.get('entry_logic', 'N/A')[:50] + '...'
    } for idx, c in enumerate(top_cases)])
    
    st.dataframe(top_df, use_container_width=True, hide_index=True)
