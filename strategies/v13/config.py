from dataclasses import dataclass

@dataclass
class V13Config:
    """V13 DeepSeek-R1 AI 交易系統配置"""
    
    # 基礎參數
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000.0
    simulation_days: int = 30
    
    # AI 決策參數
    ai_confidence_threshold: float = 0.70  # AI 最低信心門檻
    max_daily_trades: int = 3  # 每日最多交易次數
    
    # 風險管理
    base_risk: float = 0.02  # 每筆交易風險 2%
    max_leverage: float = 3.0  # 最大槓桿倍數
    max_drawdown_stop: float = 0.20  # 最大回撤停損 20%
    
    # 手續費與滑點
    fee_rate: float = 0.0004  # Binance 現貨手續費 0.04%
    slippage: float = 0.0002  # 滑點 0.02%
    
    # 訓練參數
    train_test_split: float = 0.7  # 70% 訓練，30% 測試
    
    # AI 學習參數
    enable_learning: bool = True  # 啟用從成功交易中學習
    min_profit_to_learn: float = 0.01  # 最低獲利 1% 才記錄為成功案例