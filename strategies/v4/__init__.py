# V4策略 GUI渲染入口
import streamlit as st
from .config import V4Config
from .trainer import train_model
from .backtester import run_backtest
from core.data_loader import DataLoader
from core.gui_components import render_performance_metrics, render_trade_chart

def render():
    st.header("V4 Strategy - 方向性标签与市况分类")
    
    # 加载配置
    config = V4Config()
    
    # 数据加载
    data_loader = DataLoader()
    data = data_loader.load_data(config.symbol, config.timeframe)
    
    # 训练
    if st.button("训练模型"):
        model, X, y = train_model(data, config)
        st.success("模型训练完成")
        
        # 回测
        metrics, signals = run_backtest(model, X, data, config)
        
        # 展示结果
        render_performance_metrics(metrics)
        render_trade_chart(data, signals)

def train():
    # 命令行训练入口
    config = V4Config()
    data_loader = DataLoader()
    data = data_loader.load_data(config.symbol, config.timeframe)
    model, X, y = train_model(data, config)
    print("V4模型训练完成")

def backtest():
    # 命令行回测入口
    config = V4Config()
    data_loader = DataLoader()
    data = data_loader.load_data(config.symbol, config.timeframe)
    model, X, y = train_model(data, config)
    metrics, signals = run_backtest(model, X, data, config)
    print(f"V4回测结果: {metrics}")