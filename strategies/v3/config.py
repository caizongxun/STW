from dataclasses import dataclass, asdict

@dataclass
class V3Config:
    # 基礎設定
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000.0
    
    # 標籤設定 (三重障礙法)
    pt_sl_ratio: list = None
    t_events_bars: int = 48
    
    # 模型設定 (LightGBM)
    num_leaves: int = 31
    n_estimators: int = 200
    max_depth: int = 6
    learning_rate: float = 0.01
    reg_alpha: float = 1.0     # 增加正則化，防止在雜訊中過擬合
    reg_lambda: float = 1.0
    
    # 進場與過濾閾值 (順勢接刀核心)
    signal_threshold: float = 0.55
    cooldown_bars: int = 3
    use_trend_filter: bool = True  # 核心：只做順勢的回調
    
    # 風控設定：固定風險倉位管理 (Fixed Fractional Risk)
    # 取代粗暴的固定槓桿，改為「每筆交易固定虧損總資金的 N%」
    risk_per_trade: float = 0.03   # 單筆交易最高虧損 3% (高收益預設)
    max_leverage: int = 20         # 允許的最高槓桿上限
    
    atr_sl_multiplier: float = 1.5 # 止損乘數
    atr_tp_multiplier: float = 4.0 # 追求極致盈虧比 (1:2.6以上)
    fee_rate: float = 0.0004
    slippage: float = 0.0002
    
    def __post_init__(self):
        if self.pt_sl_ratio is None:
            self.pt_sl_ratio = [3.0, 1.5] # 訓練目標也要大賺小賠
            
    def to_dict(self):
        d = asdict(self)
        d['pt_sl_ratio'] = list(d['pt_sl_ratio'])
        return d