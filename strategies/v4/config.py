from dataclasses import dataclass

@dataclass
class V4Config:
    # 基礎設定
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000.0
    
    # HTF (高時間框架) 趨勢過濾
    ema_trend: int = 200
    
    # FVG 品質過濾 (核心優化)
    fvg_min_size_atr: float = 0.5  # FVG 的缺口大小必須至少有 0.5 倍 ATR (避免無意義的小缺口)
    fvg_max_age: int = 8           # 縮短有效期，趁熱吃
    
    # Liquidity Sweep (流動性掠奪)
    require_sweep: bool = True     # 是否要求在形成 FVG 前，必須先掃過近期的流動性(前高/前低)
    sweep_lookback: int = 15       # 尋找前高前低的區間
    
    # 風控設定
    risk_per_trade: float = 0.015  # 單筆風險 1.5%
    max_leverage: int = 15
    
    # 盈虧比設定
    risk_reward_ratio: float = 2.5 # 調降至 2.5，提高勝率
    breakeven_r: float = 1.0       # 更早保本，只要跑出 1R 的獲利就設為不虧
    
    fee_rate: float = 0.0004
    slippage: float = 0.0002
    
    cooldown_bars: int = 5