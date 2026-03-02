from dataclasses import dataclass

@dataclass
class V9Config:
    """V9 趨勢回調狙擊手配置"""
    
    # 基礎設定
    symbol: str = 'BTCUSDT'
    capital: float = 10000.0
    simulation_days: int = 60
    
    # 進場條件
    rsi_threshold: int = 35
    pullback_to_ema: str = 'EMA50'
    trend_ema: int = 200
    
    # 分批止盈設定
    tp1_r: float = 1.0
    tp2_r: float = 2.5
    partial_tp_pct: float = 0.5
    
    # 風險管理
    base_risk: float = 0.02
    max_leverage: int = 3
    atr_multiplier: float = 1.5
    
    # 手續費
    fee_rate: float = 0.0005
    slippage: float = 0.0003
    
    # 交易限制
    max_daily_trades: int = 10
    cooldown_bars: int = 3
    max_drawdown_stop: float = 0.25