from dataclasses import dataclass

@dataclass
class V4Config:
    # 基礎設定
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000.0
    
    # 趨勢過濾與進場指標
    ema_fast: int = 50
    ema_slow: int = 200
    
    # RSI 放棄，改用更精確的布林帶或 ATR 乖離
    rsi_period: int = 14
    rsi_oversold: int = 40    
    rsi_overbought: int = 60  
    
    # 價格行為過濾
    use_price_action: bool = True  
    
    # 風控設定 (降低風險，每次只拿1%去試錯)
    risk_per_trade: float = 0.01   
    max_leverage: int = 10         
    
    atr_period: int = 14
    atr_sl_multiplier: float = 1.0 # 砍掉那些拖泥帶水的單子，不對就跑
    atr_tp_multiplier: float = 3.0 # 目標 1:3
    
    fee_rate: float = 0.0004
    slippage: float = 0.0002
    
    cooldown_bars: int = 8         # 增加冷卻期，防止連續挨打
    max_hold_bars: int = 48        # 縮短時間止損 (12小時沒噴就走人)