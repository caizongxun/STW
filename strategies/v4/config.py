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
    rsi_period: int = 14
    rsi_oversold: int = 35    # 放寬超賣標準 (在強勢多頭中，RSI可能跌到40就反轉了)
    rsi_overbought: int = 65  # 放寬超買標準
    
    # 價格行為過濾
    use_price_action: bool = True  # 是否必須要有下影線/上影線確認
    
    # 風控設定 (固定風險倉位管理)
    risk_per_trade: float = 0.03   # 單筆交易最高虧損 3%
    max_leverage: int = 20         # 允許的最高槓桿上限
    
    atr_period: int = 14
    atr_sl_multiplier: float = 1.5 # 止損乘數
    atr_tp_multiplier: float = 4.0 # 止盈乘數
    
    fee_rate: float = 0.0004
    slippage: float = 0.0002
    
    cooldown_bars: int = 3
    max_hold_bars: int = 96        # 時間止損 (約24小時)