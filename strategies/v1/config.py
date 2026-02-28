from dataclasses import dataclass

@dataclass
class V1Config:
    # 基础
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000
    
    # 標籤
    forward_bars: int = 8
    min_return_pct: float = 0.008  # 0.8%
    
    # 模型
    model_type: str = 'xgboost'
    max_depth: int = 6
    
    # 回测
    leverage: int = 3
    position_pct: float = 0.3