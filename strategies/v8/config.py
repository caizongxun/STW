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
    train_size_pct: float = 0.7           # 70% 用於訓練
    lstm_lookback: int = 60               # 使用過去 60 根 K 線預測
    lstm_forecast_bars: int = 6           # 預測未來 6 根 K 線（15m * 6 = 1.5h）
    lstm_confidence: float = 0.80         # 信心度閾值 80%
    lstm_epochs: int = 50                 # 訓練輪數
    lstm_batch_size: int = 32
    
    # 雙時間框架設定
    enable_dual_timeframe: bool = True    # 啟用 15m + 1h 雙時間框架
    
    # 反轉形態過濾
    enable_pattern_filter: bool = True
    
    # 反轉定義參數
    reversal_threshold: float = 0.02      # 未來最小漲幅 2%
    reversal_stop_mult: float = 1.5       # 止損倍數
    
    # 風險管理
    base_risk: float = 0.02               # 2%
    max_leverage: int = 3
    atr_multiplier: float = 1.5           # 止損 ATR 倍數
    tp_ratio: float = 2.5                 # 止盈倍數
    trailing_stop_trigger: float = 1.5    # 1.5R 時啟動移動止盈
    
    # 手續費
    fee_rate: float = 0.0005
    slippage: float = 0.0003
    
    # 交易限制
    max_daily_trades: int = 15
    cooldown_bars: int = 4
    max_drawdown_stop: float = 0.20