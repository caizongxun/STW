# GUI共用組件
import streamlit as st
import pandas as pd
import plotly.express as px

def render_performance_metrics(metrics):
    """渲染性能指标"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("月化报酬率", f"{metrics['monthly_return']:.2%}")
    with col2:
        st.metric("胜率", f"{metrics['win_rate']:.2%}")
    with col3:
        st.metric("盈亏比", f"{metrics['profit_factor']:.2f}")
    with col4:
        st.metric("最大回撤", f"{metrics['max_drawdown']:.2%}")

def render_trade_chart(data, signals):
    """渲染交易图表"""
    df = data.copy()
    df["signal"] = signals
    
    fig = px.line(df, x="open_time", y="close", title="价格与交易信号")
    
    # 添加做多信号
    long_signals = df[df["signal"] == 1]
    fig.add_scatter(x=long_signals["open_time"], y=long_signals["close"], 
                   mode="markers", marker=dict(color="green", size=10), name="做多")
    
    # 添加做空信号
    short_signals = df[df["signal"] == -1]
    fig.add_scatter(x=short_signals["open_time"], y=short_signals["close"], 
                   mode="markers", marker=dict(color="red", size=10), name="做空")
    
    st.plotly_chart(fig, use_container_width=True)