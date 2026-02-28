import numpy as np
import pandas as pd

def generate_labels(data, config):
    df = data.copy()
    
    # 计算未来收益
    forward_returns = df["close"].pct_change(config.forward_bars).shift(-config.forward_bars)
    
    # 生成标签
    labels = np.where(forward_returns > config.min_return_pct, 1,
                     np.where(forward_returns < -config.min_return_pct, -1, 0))
    
    return labels