from dataclasses import dataclass, asdict

@dataclass
class V3Config:
    # 基礎設定
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000.0
    
    # 標籤設定 (三重障礙法 Triple Barrier Method)
    pt_sl_ratio: list = None  # [止盈乘數, 止損乘數]
    t_events_bars: int = 48  # 時間障礙 
    min_return: float = 0.005 # 最小收益率過濾
    
    # 特徵設定
    use_multi_tf: bool = True
    use_volume_features: bool = True
    
    # 模型設定 (LightGBM)
    num_leaves: int = 31
    n_estimators: int = 150
    max_depth: int = 6
    learning_rate: float = 0.03
    reg_alpha: float = 0.5
    
    # 交易與風控閾值 (二次優化重點)
    signal_threshold: float = 0.65 # 進場概率閾值 (提高以減少假陽性)
    cooldown_bars: int = 5         # 交易冷卻期，避免頻繁開平倉
    
    # 風控與回測設定
    leverage: int = 3
    position_pct: float = 0.1      # 固定比例倉位管理 (最大10%)
    atr_sl_multiplier: float = 1.5
    atr_tp_multiplier: float = 2.0
    fee_rate: float = 0.0006       # 雙邊萬分之六(Taker)
    slippage: float = 0.0005       # 滑點萬分之五
    
    def __post_init__(self):
        if self.pt_sl_ratio is None:
            self.pt_sl_ratio = [1.5, 1.5]
            
    def to_dict(self):
        d = asdict(self)
        d['pt_sl_ratio'] = list(d['pt_sl_ratio'])
        return d