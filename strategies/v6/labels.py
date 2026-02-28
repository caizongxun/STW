import numpy as np
import pandas as pd

def generate_labels(data, config):
    df = data.copy()
    
    # 计算未来收益
    forward_returns = df["close"].pct_change(config.forward_bars).shift(-config.forward_bars)
    
    # 考虑交易成本（佣金+滑点）
    transaction_cost = 0.002  # 0.2%的交易成本
    min_profit = config.min_return_pct + transaction_cost
    
    # 生成标签
    labels = np.where(forward_returns > min_profit, 1,
                     np.where(forward_returns < -min_profit, -1, 0))
    
    # 如果启用市况过滤，只在趋势市场生成信号
    if config.market_filter:
        # 使用1h的MA20和MA50判断趋势
        trend = np.where(df["1h_sma_20"] > df["1h_sma_50"], 1,
                        np.where(df["1h_sma_20"] < df["1h_sma_50"], -1, 0))
        # 只在趋势方向一致时生成信号
        labels = np.where((labels == 1) & (trend == 1), 1,
                         np.where((labels == -1) & (trend == -1), -1, 0))
    
    return labels