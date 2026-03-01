from dataclasses import dataclass

@dataclass
class V7Config:
    """V7 高勝率技術組合配置"""
    
    # 基礎設定
    symbol: str = 'BTCUSDT'
    capital: float = 1000.0
    simulation_days: int = 30
    
    # 策略啟用（保留以便 UI 相容）
    enable_momentum: bool = True
    enable_liquidity_hunt: bool = True
    enable_ml_filter: bool = True
    
    # 風險管理
    base_risk: float = 0.025              # 提高到 2.5%
    max_leverage: int = 4                 # 提高到 4 倍
    enable_compound: bool = True
    
    # 複利加速器
    compound_profit_threshold_1: float = 0.10
    compound_profit_threshold_2: float = 0.20
    compound_loss_threshold: float = -0.05
    risk_multiplier_profit_1: float = 1.5
    risk_multiplier_profit_2: float = 2.0
    risk_multiplier_loss: float = 0.5
    
    # ML 參數（保留以便 UI 相容）
    ml_confidence_threshold: float = 0.75
    lstm_lookback: int = 60
    lstm_forecast_bars: int = 4
    
    # 動量突破參數（未使用）
    momentum_atr_multiplier: float = 1.5
    momentum_volume_threshold: float = 1.5
    momentum_tp_r: float = 2.5            # 提高到 2.5
    momentum_sl_r: float = 1.0
    
    # 流動性掃蕩參數（未使用）
    liquidity_wick_ratio: float = 0.6
    liquidity_reversal_bars: int = 3
    liquidity_tp_r: float = 3.0
    liquidity_sl_r: float = 1.0
    
    # 手續費
    fee_rate: float = 0.0005
    slippage: float = 0.0003
    
    # 交易限制
    max_daily_trades: int = 20            # 降低到 20 筆
    cooldown_bars: int = 3                # 增加冷卻期
    max_drawdown_stop: float = 0.25