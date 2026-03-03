from dataclasses import dataclass

@dataclass
class V11Config:
    """V11 AI 模型配置"""
    
    symbol: str = 'BTCUSDT'
    capital: float = 10000.0
    simulation_days: int = 90
    
    # AI 參數
    ai_confidence_threshold: float = 0.65  # AI 預測上漲機率大於此值才進場
    look_forward_bars: int = 10            # 預測未來 N 根 K 線的漲跌
    train_test_split: float = 0.4          # 前 40% 數據用於訓練 AI，後 60% 用於交易測試
    
    # 出場與風險
    tp_r: float = 2.0
    atr_multiplier: float = 1.5
    base_risk: float = 0.02
    max_leverage: int = 3
    
    # 手續費
    fee_rate: float = 0.0005
    slippage: float = 0.0003
    max_drawdown_stop: float = 0.25