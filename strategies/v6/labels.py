import numpy as np
import pandas as pd

def generate_labels(data, config):
    df = data.copy()
    
    # 计算未来收益
    forward_returns = df["close"].pct_change(config.forward_bars).shift(-config.forward_bars)
    
    # 考虑交易成本后的真实收益
    min_return = config.min_return_pct + (2 * 0.001) + (2 * 0.0005)  # 佣金+滑点
    
    # 生成标签
    labels = np.where(forward_returns > min_return, 1,
                     np.where(forward_returns < -min_return, -1, 0))
    
    return labels