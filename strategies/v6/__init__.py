# V6策略 GUI渲染入口
import streamlit as st
import pandas as pd
from .config import V6Config
from .trainer import train_model
from .backtester import run_backtest
from core.data_loader import DataLoader
from core.gui_components import render_performance_metrics, render_trade_chart

def render():
    st.header("V6 Strategy - 多时间框架融合与智能风控")
    
    # 加载配置
    config = V6Config()
    
    # 配置参数调整
    st.sidebar.subheader("策略配置")
    config.symbol = st.sidebar.selectbox("交易对", ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"])
    config.timeframe = st.sidebar.selectbox("时间框架", ["15m", "1h", "1d"])
    config.capital = st.sidebar.number_input("初始资金", min_value=1000, max_value=100000, value=10000)
    config.leverage = st.sidebar.slider("杠杆倍数", min_value=1, max_value=10, value=3)
    config.position_pct = st.sidebar.slider("仓位比例", min_value=0.1, max_value=1.0, value=0.3)
    
    # 模型配置
    config.use_lstm = st.sidebar.checkbox("使用LSTM模型", value=False)
    if config.use_lstm:
        config.lstm_units = st.sidebar.slider("LSTM单元数", min_value=32, max_value=128, value=50)
        config.dropout_rate = st.sidebar.slider("Dropout率", min_value=0.1, max_value=0.5, value=0.2)
    else:
        config.max_depth = st.sidebar.slider("XGBoost最大深度", min_value=3, max_value=10, value=6)
    
    # 风控配置
    config.dynamic_stop_loss = st.sidebar.checkbox("启用动态止损", value=True)
    if config.dynamic_stop_loss:
        config.stop_loss_multiplier = st.sidebar.slider("止损倍数(ATR)", min_value=1.0, max_value=5.0, value=2.0)
    config.market_filter = st.sidebar.checkbox("启用市况过滤", value=True)
    
    # 数据加载
    data_loader = DataLoader()
    data = data_loader.load_data(config.symbol, config.timeframe)
    st.subheader(f"数据预览 ({config.symbol} {config.timeframe})")
    st.dataframe(data.tail(10))
    
    # 训练和回测
    tab1, tab2 = st.tabs(["训练模型", "回测结果"])
    with tab1:
        if st.button("开始训练"):
            with st.spinner("正在训练模型..."):
                model, X, y, scaler = train_model(data, config)
                st.success("模型训练完成！")
                st.session_state["v6_model"] = model
                st.session_state["v6_scaler"] = scaler
                st.session_state["v6_X"] = X
                st.session_state["v6_data"] = data
                st.session_state["v6_config"] = config
    
    with tab2:
        if "v6_model" in st.session_state:
            model = st.session_state["v6_model"]
            scaler = st.session_state["v6_scaler"]
            X = st.session_state["v6_X"]
            data = st.session_state["v6_data"]
            config = st.session_state["v6_config"]
            
            if st.button("开始回测"):
                with st.spinner("正在回测..."):
                    metrics, signals, account_value, trades = run_backtest(model, X, data, config, scaler)
                    st.subheader("回测指标")
                    render_performance_metrics(metrics)
                    
                    st.subheader("资金曲线")
                    # 对齐资金曲线和时间
                    time_index = data["open_time"].iloc[len(data)-len(account_value):]
                    st.line_chart(pd.DataFrame({
                        "时间": time_index,
                        "账户价值": account_value
                    }).set_index("时间"))
                    
                    st.subheader("交易信号")
                    render_trade_chart(data, signals)
                    
                    st.subheader("交易记录")
                    st.dataframe(pd.DataFrame(trades))
        else:
            st.info("请先训练模型")

def train():
    # 命令行训练入口
    config = V6Config()
    data_loader = DataLoader()
    data = data_loader.load_data(config.symbol, config.timeframe)
    model, X, y, scaler = train_model(data, config)
    print("V6模型训练完成")

def backtest():
    # 命令行回测入口
    config = V6Config()
    data_loader = DataLoader()
    data = data_loader.load_data(config.symbol, config.timeframe)
    model, X, y, scaler = train_model(data, config)
    metrics, signals, account_value, trades = run_backtest(model, X, data, config, scaler)
    print(f"V6回测结果: {metrics}")
    print(f"总交易次数: {len(trades)}")
    print(f"最终账户价值: {account_value[-1]}")