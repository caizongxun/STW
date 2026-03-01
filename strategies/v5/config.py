from dataclasses import dataclass

@dataclass
class V5Config:
    """V5 配對交易策略配置"""
    
    # 交易對設定
    symbol_long: str = 'ETHUSDT'   # 做多的幣種
    symbol_short: str = 'BTCUSDT'  # 做空的幣種
    timeframe: str = '1h'
    capital: float = 10000.0
    
    # 回測設定
    simulation_days: int = 90
    
    # 價差統計參數
    lookback_days: int = 30        # 計算過去 N 天的價差均值與標準差
    entry_zscore: float = 2.0      # 價差偏離 2 個標準差時開倉
    exit_zscore: float = 0.5       # 價差回歸到 0.5 個標準差時平倉
    stop_zscore: float = 3.0       # 價差持續偏離到 3 個標準差時強制止損
    
    # 資金管理
    risk_per_trade: float = 0.02   # 單筆風險 2%
    max_leverage: int = 5          # 最大槓桿 5 倍（配對交易通常不需要高槓桿）
    
    # 手續費與滑點
    fee_rate: float = 0.0005
    slippage: float = 0.0003
    
    # 持倉限制
    max_positions: int = 3         # 最多同時持有 3 對配對倉位
    cooldown_bars: int = 5         # 平倉後冷卻 5 根 K 線再開新倉