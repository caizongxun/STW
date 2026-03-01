from dataclasses import dataclass

@dataclass
class V4Config:
    # 基礎設定
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000.0
    
    # ICT / SMC 核心設定
    ema_trend: int = 200           # 用於過濾大級別方向 (ICT 偏好順著HTF結構做)
    fvg_max_age: int = 12          # FVG 有效期 (超過 N 根 K 線未被填補則失效)
    
    # 風控與盈虧比 (SMC 標配：固定風險，高盈虧比)
    risk_per_trade: float = 0.02   # 單筆交易固定虧損 2%
    max_leverage: int = 20         
    
    risk_reward_ratio: float = 3.0 # 固定盈虧比 (預設 1:3)
    breakeven_r: float = 1.5       # 當獲利達到 1.5R 時，將止損推至保本
    
    fee_rate: float = 0.0004
    slippage: float = 0.0002
    
    cooldown_bars: int = 3         # 交易冷卻期