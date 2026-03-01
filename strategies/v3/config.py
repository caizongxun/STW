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
    min_return: float = 0.005  # 加入遺失的屬性，用於 labels.py 中的防呆
    
    # 模型設定 (LightGBM)
    num_leaves: int = 31
    n_estimators: int = 200
    max_depth: int = 6
    learning_rate: float = 0.01
    reg_alpha: float = 1.0     
    reg_lambda: float = 1.0
    
    # 進場與過濾閾值 (順勢接刀核心)
    signal_threshold: float = 0.55
    cooldown_bars: int = 3
    use_trend_filter: bool = True  
    
    # 風控設定：固定風險倉位管理 
    risk_per_trade: float = 0.03   
    max_leverage: int = 20         
    
    atr_sl_multiplier: float = 1.5 
    atr_tp_multiplier: float = 4.0 
    fee_rate: float = 0.0004
    slippage: float = 0.0002
    
    def __post_init__(self):
        if self.pt_sl_ratio is None:
            self.pt_sl_ratio = [3.0, 1.5] 
            
    def to_dict(self):
        d = asdict(self)
        d['pt_sl_ratio'] = list(d['pt_sl_ratio'])
        return d