from dataclasses import dataclass

@dataclass
class V7Config:
    """V7 AI 驅動多策略引擎配置"""
    
    # 基礎設定
    symbol: str = 'BTCUSDT'
    capital: float = 1000.0
    simulation_days: int = 30
    
    # 策略啟用開關
    enable_momentum: bool = True          # 動量突破剝頭皮
    enable_liquidity_hunt: bool = True    # 流動性掃蕩反轉
    enable_ml_filter: bool = True         # AI 過濾器
    
    # 風險管理
    base_risk: float = 0.02               # 基礎單筆風險 2%
    max_leverage: int = 3                 # 最大槓桿 3 倍
    enable_compound: bool = True          # 複利加速器
    
    # 複利加速器參數
    compound_profit_threshold_1: float = 0.10  # 盈利 10% 時風險提升
    compound_profit_threshold_2: float = 0.20  # 盈利 20% 時風險再提升
    compound_loss_threshold: float = -0.05     # 虧損 5% 時風險降低
    risk_multiplier_profit_1: float = 1.5      # 盈利 10% 時風險 x1.5
    risk_multiplier_profit_2: float = 2.0      # 盈利 20% 時風險 x2.0
    risk_multiplier_loss: float = 0.5          # 虧損 5% 時風險 x0.5
    
    # ML 模型參數
    ml_confidence_threshold: float = 0.75  # AI 信心度閾值 75%
    lstm_lookback: int = 60                # LSTM 回顧 60 根 K 線
    lstm_forecast_bars: int = 4            # 預測未來 4 根 K 線（1 小時）
    
    # 動量突破參數
    momentum_atr_multiplier: float = 1.5   # 突破幅度需超過 1.5 倍 ATR
    momentum_volume_threshold: float = 1.5 # 成交量需為平均的 1.5 倍
    momentum_tp_r: float = 2.0             # 止盈 2R
    momentum_sl_r: float = 1.0             # 止損 1R
    
    # 流動性掃蕩參數
    liquidity_wick_ratio: float = 0.6      # 影線長度需超過實體的 60%
    liquidity_reversal_bars: int = 3       # 反轉確認需 3 根 K 線
    liquidity_tp_r: float = 3.0            # 止盈 3R
    liquidity_sl_r: float = 1.0            # 止損 1R
    
    # 手續費與滑點
    fee_rate: float = 0.0005
    slippage: float = 0.0003
    
    # 交易限制
    max_daily_trades: int = 30             # 每日最多 30 筆交易
    cooldown_bars: int = 2                 # 平倉後冷卻 2 根 K 線
    max_drawdown_stop: float = 0.25        # 當回撤超過 25% 時停止交易