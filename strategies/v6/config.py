from dataclasses import dataclass

@dataclass
class V6Config:
    # 基礎
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000
    
    # 標籤
    forward_bars: int = 8
    min_return_pct: float = 0.015  # 1.5%
    
    # 模型
    model_type: str = 'xgboost'
    max_depth: int = 6
    # 新增的模型参数
    use_lstm: bool = False
    lstm_units: int = 50
    dropout_rate: float = 0.2
    
    # 回測
    leverage: int = 3
    position_pct: float = 0.3
    # 新增的风控参数
    dynamic_stop_loss: bool = True
    stop_loss_multiplier: float = 2.0
    market_filter: bool = True