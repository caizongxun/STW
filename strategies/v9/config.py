from dataclasses import dataclass

@dataclass
class V9Config:
    """V9 趨勢回調狙擊手配置"""
    
    symbol: str = 'BTCUSDT'
    capital: float = 10000.0
    simulation_days: int = 60
    
    # 出場模式: 'partial_tp', 'smc_runner', 'trailing'
    exit_mode: str = 'trailing'
    
    # 出場參數
    tp1_r: float = 1.5           # Partial模式的TP1，或Trailing模式的啟動點
    tp2_r: float = 4.0           # 最終目標極限
    partial_tp_pct: float = 0.0  # 平倉比例
    
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