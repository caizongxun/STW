from dataclasses import dataclass, asdict

@dataclass
class V3Config:
    # 基礎設定
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000.0
    
    # 標籤設定 (三重障礙法 Triple Barrier Method)
    pt_sl_ratio: list = None  # 追求高盈虧比
    t_events_bars: int = 48
    min_return: float = 0.005
    
    # 特徵設定
    use_multi_tf: bool = True
    use_volume_features: bool = True
    
    # 模型設定 (LightGBM)
    num_leaves: int = 63      # 增加模型複雜度以捕捉非線性特徵
    n_estimators: int = 300
    max_depth: int = 8
    learning_rate: float = 0.02
    reg_alpha: float = 0.2
    
    # 交易與風控閾值 (進攻型設定)
    signal_threshold: float = 0.58 # 降低閾值，捕捉更多波段機會
    cooldown_bars: int = 2         # 縮短冷卻期，不錯過連續機會
    
    # 風控與回測設定 (為了每月30%的目標，需拉高資金利用率與槓桿)
    leverage: int = 10             # 拉高槓桿至 10 倍 (合約標準)
    position_pct: float = 0.50     # 每次動用 50% 倉位 (極具攻擊性)
    atr_sl_multiplier: float = 1.2 # 收緊止損，砍掉不對的單
    atr_tp_multiplier: float = 3.5 # 放大止盈，吃滿大波段 (盈虧比近 1:3)
    fee_rate: float = 0.0004       # 假設使用限價單(Maker)+市價單混合 萬分之四
    slippage: float = 0.0002       # 滑點萬分之二
    
    def __post_init__(self):
        if self.pt_sl_ratio is None:
            self.pt_sl_ratio = [3.0, 1.0] # 訓練目標：大賺小賠
            
    def to_dict(self):
        d = asdict(self)
        d['pt_sl_ratio'] = list(d['pt_sl_ratio'])
        return d