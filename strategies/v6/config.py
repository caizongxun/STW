from dataclasses import dataclass

@dataclass
class V6Config:
    # 基础
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000
    
    # 標籤
    forward_bars: int = 8
    min_return_pct: float = 0.015  # 1.5%
    
    # 模型
    model_type: str = 'xgboost_lstm'
    max_depth: int = 6
    dual_model: bool = True
    long_model_threshold: float = 0.75
    short_model_threshold: float = 0.75
    market_condition_filter: bool = True
    multi_timeframe: bool = True
    
    # 回测
    leverage: int = 3
    position_pct: float = 0.3
    risk_management: bool = True
    kelly_positioning: bool = True
    signal_strength_threshold: float = 0.5
    dynamic_stop_loss: bool = True