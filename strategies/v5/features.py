import pandas as pd
import numpy as np
import talib

class V5FeatureEngine:
    """V5 配對交易特徵生成引擎"""
    
    def __init__(self, config):
        self.config = config
        
    def generate(self, df_long, df_short):
        """生成配對交易所需的價差特徵"""
        
        # 確保兩個 DataFrame 有相同的時間索引
        df_long = df_long.copy()
        df_short = df_short.copy()
        
        # 合併數據（按時間對齊）
        df = pd.DataFrame({
            'open_time': df_long['open_time'],
            'price_long': df_long['close'],
            'price_short': df_short['close']
        })
        
        # 計算價格比率（Spread Ratio）
        # 例如：ETH/BTC 的比率
        df['spread'] = df['price_long'] / df['price_short']
        
        # 計算 Z-Score（標準化價差）
        # Z-Score = (當前價差 - 平均價差) / 標準差
        lookback_bars = self._days_to_bars(self.config.lookback_days)
        df['spread_mean'] = df['spread'].rolling(window=lookback_bars).mean()
        df['spread_std'] = df['spread'].rolling(window=lookback_bars).std()
        
        # 計算 Z-Score
        df['zscore'] = (df['spread'] - df['spread_mean']) / df['spread_std']
        
        # 計算 ATR（用於動態止損）
        df['atr_long'] = talib.ATR(df_long['high'], df_long['low'], df_long['close'], timeperiod=14)
        df['atr_short'] = talib.ATR(df_short['high'], df_short['low'], df_short['close'], timeperiod=14)
        
        # 清理無效數據
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna().reset_index(drop=True)
        
        return df
    
    def _days_to_bars(self, days):
        """將天數轉換為 K 線根數"""
        if self.config.timeframe == '15m':
            return days * 96  # 一天 96 根 15 分鐘 K 線
        elif self.config.timeframe == '1h':
            return days * 24
        elif self.config.timeframe == '4h':
            return days * 6
        else:
            return days * 24  # 預設 1 小時