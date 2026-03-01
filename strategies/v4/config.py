from dataclasses import dataclass

@dataclass
class V4Config:
    # 基礎設定
    symbol: str = 'BTCUSDT'
    timeframe: str = '15m'
    capital: float = 10000.0
    
    # 回測天數設定 (0 = 跑全部歷史資料)
    simulation_days: int = 0
    
    # 資金管理：複利模式
    use_compounding: bool = True   
    risk_per_trade: float = 0.03   
    max_leverage: int = 30         # 允許更高的槓桿來支撐緊湊的止損
    
    # 時間過濾 (Kill Zones) - 避開亞洲垃圾時間
    use_killzones: bool = True     
    
    # HTF (高時間框架) 趨勢過濾
    ema_trend: int = 200
    
    # FVG 品質過濾
    fvg_min_size_atr: float = 0.5  
    fvg_max_age: int = 8           
    
    # Liquidity Sweep
    require_sweep: bool = True     
    sweep_lookback: int = 15       
    
    # 盈虧比設定
    risk_reward_ratio: float = 2.5 
    breakeven_r: float = 1.0       
    
    fee_rate: float = 0.0004
    slippage: float = 0.0002
    
    cooldown_bars: int = 5