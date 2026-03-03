from dataclasses import dataclass

@dataclass
class V12Config:
    """V12 高級量化模型配置"""
    
    symbol: str = 'BTCUSDT'
    capital: float = 10000.0
    simulation_days: int = 120
    
    # 交易頻率與屏障設定
    max_daily_trades: int = 2
    look_forward_bars: int = 36    # 往未來尋找屏障的K線數 (15m * 36 = 9小時)
    tp_atr_mult: float = 2.0       # 止盈屏障距離
    sl_atr_mult: float = 1.0       # 止損屏障距離
    
    # AI 訓練設定
    train_test_split: float = 0.5  # 50% 訓練, 50% 測試
    
    # 風險管理
    base_risk: float = 0.02
    max_leverage: int = 3
    fee_rate: float = 0.0005
    slippage: float = 0.0003
    max_drawdown_stop: float = 0.25