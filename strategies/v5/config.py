from dataclasses import dataclass

@dataclass
class V5Config:
    """V5 配對交易策略配置"""
    
    # 交易對設定
    symbol_long: str = 'ETHUSDT'
    symbol_short: str = 'BTCUSDT'
    timeframe: str = '1h'
    capital: float = 10000.0
    
    # 回測設定
    simulation_days: int = 90
    
    # 價差統計參數（優化：縮短回顧週期）
    lookback_days: int = 14        # 從 30 天縮短到 14 天，提高對近期趨勢的敏感度
    entry_zscore: float = 1.5      # 降低進場閾值到 1.5，提高交易頻率
    exit_zscore: float = 0.3       # 縮緊出場閾值到 0.3，更快獲利了結
    stop_zscore: float = 2.5       # 縮緊止損閾值，避免被套太久
    
    # 加入動量確認（關鍵優化）
    use_momentum_filter: bool = True  # 只有當價差開始回歸時才開倉
    
    # 資金管理
    risk_per_trade: float = 0.03   # 提高到 3%，因為配對交易風險較低
    max_leverage: int = 3          # 降低槓桿到 3 倍，減少資金成本
    
    # 手續費與滑點
    fee_rate: float = 0.0005
    slippage: float = 0.0003
    
    # 持倉限制
    max_positions: int = 2         # 減少同時持倉數，提高資金利用率
    cooldown_bars: int = 3
    
    # 最大持倉時間（防止被套太久）
    max_holding_bars: int = 168    # 1 小時級別最多持有 168 小時 (7 天)