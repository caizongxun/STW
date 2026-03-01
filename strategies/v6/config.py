from dataclasses import dataclass

@dataclass
class V6Config:
    """V6 資金費率套利策略配置"""
    
    # 基礎設定
    symbol: str = 'BTCUSDT'
    capital: float = 10000.0
    simulation_days: int = 90
    
    # 資金費率閾值
    min_funding_rate: float = 0.01 / 100  # 0.01% (每 8 小時)
    # 說明：Binance 資金費率通常在 0.01% ~ 0.1% 之間
    # 牛市時可能高達 0.3%（年化 300%+）
    # 熊市時可能為負（-0.05%）
    
    # 資金分配
    allocation_pct: float = 0.5  # 每次套利使用 50% 資金
    max_positions: int = 3       # 最多同時 3 組套利
    
    # 對沖管理
    enable_hedge_rebalance: bool = True  # 啟用對沖再平衡
    rebalance_threshold: float = 0.02     # 當對沖偏離 2% 時重新平衡
    max_basis_pct: float = 0.02           # 最大基差容忍 2%
    
    # 手續費（現貨 + 合約雙邊）
    spot_fee_rate: float = 0.001   # 現貨手續費 0.1%
    futures_fee_rate: float = 0.0005  # 合約手續費 0.05%
    
    # 風險控制
    stop_loss_pct: float = 0.05    # 單次套利最大虧損 5%
    min_holding_hours: int = 24    # 最少持有 24 小時（收取至少 3 次資金費率）