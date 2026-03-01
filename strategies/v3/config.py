from dataclasses import dataclass, asdict

@dataclass
class V3Config:
    # 基礎設定
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000.0
    
    # 標籤設定 (三重障礙法 Triple Barrier Method)
    pt_sl_ratio: list = None  # [止盈乘數, 止損乘數]
    t_events_bars: int = 96  # 時間障礙 (例如 24小時 = 96 * 15m)
    min_return: float = 0.01 # 最小收益率過濾
    
    # 特徵設定
    use_multi_tf: bool = True
    use_volume_features: bool = True
    
    # 模型設定 (LightGBM)
    num_leaves: int = 31
    n_estimators: int = 100
    max_depth: int = 5
    learning_rate: float = 0.05
    reg_alpha: float = 0.1
    
    # 交易閾值
    signal_threshold: float = 0.7 # 進場概率閾值
    
    # 風控與回測設定
    leverage: int = 3
    position_pct: float = 0.3
    atr_sl_multiplier: float = 2.0
    atr_tp_multiplier: float = 3.0
    fee_rate: float = 0.001
    slippage: float = 0.0005
    
    def __post_init__(self):
        if self.pt_sl_ratio is None:
            self.pt_sl_ratio = [2.0, 2.0] # 預設止盈止損為 2 ATR
            
    def to_dict(self):
        d = asdict(self)
        d['pt_sl_ratio'] = list(d['pt_sl_ratio'])
        return d