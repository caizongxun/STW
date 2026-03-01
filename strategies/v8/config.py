from dataclasses import dataclass

@dataclass
class V8Config:
    """V8 LSTM 反轉預測策略配置"""
    
    # 基礎設定
    symbol: str = 'BTCUSDT'
    capital: float = 10000.0
    simulation_days: int = 60
    
    # LSTM 模型設定
    train_model: bool = True
    train_size_pct: float = 0.7
    lstm_lookback: int = 60
    lstm_forecast_bars: int = 6
    lstm_confidence: float = 0.65          # 降低到 65%
    lstm_epochs: int = 50
    lstm_batch_size: int = 32
    
    # 雙時間框架設定
    enable_dual_timeframe: bool = True
    
    # 反轉形態過濾
    enable_pattern_filter: bool = False    # 預設關閉
    
    # 反轉定義參數
    reversal_threshold: float = 0.015      # 降低到 1.5%
    reversal_stop_mult: float = 1.2        # 降低到 1.2
    
    # 風險管理
    base_risk: float = 0.025
    max_leverage: int = 3
    atr_multiplier: float = 1.2            # 降低到 1.2
    tp_ratio: float = 2.5
    trailing_stop_trigger: float = 1.5
    
    # 手續費
    fee_rate: float = 0.0005
    slippage: float = 0.0003
    
    # 交易限制
    max_daily_trades: int = 20
    cooldown_bars: int = 2                 # 降低到 2
    max_drawdown_stop: float = 0.20