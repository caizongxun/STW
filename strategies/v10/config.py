from dataclasses import dataclass

@dataclass
class V10Config:
    """V10 波動爆發狙擊手配置"""
    
    symbol: str = 'BTCUSDT'
    capital: float = 10000.0
    simulation_days: int = 60
    
    # 擠壓與突破參數
    squeeze_length: int = 20        # 比較過去 N 根 K 線的帶寬
    rsi_momentum: int = 60          # 突破時 RSI 必須大於此值 (強動能)
    volume_surge: float = 1.5       # 成交量必須大於均量的倍數
    
    # 出場模式
    exit_mode: str = 'ema_trailing' # 'ema_trailing' 或 'fixed_rr'
    tp_r: float = 2.5               # fixed_rr 模式下的盈虧比目標
    
    # 風險管理
    base_risk: float = 0.02
    max_leverage: int = 3
    
    # 手續費
    fee_rate: float = 0.0005
    slippage: float = 0.0003
    
    # 限制
    cooldown_bars: int = 5
    max_drawdown_stop: float = 0.25