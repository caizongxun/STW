import pandas as pd
import numpy as np
import talib

class V5FeatureEngine:
    """V5 配對交易特徵生成引擎"""
    
    def __init__(self, config):
        self.config = config
        
    def generate(self, df_long, df_short):
        """生成配對交易所需的價差特徵"""
        
        df_long = df_long.copy()
        df_short = df_short.copy()
        
        df = pd.DataFrame({
            'open_time': df_long['open_time'],
            'price_long': df_long['close'],
            'price_short': df_short['close']
        })
        
        # 計算價格比率
        df['spread'] = df['price_long'] / df['price_short']
        
        # 計算 Z-Score
        lookback_bars = self._days_to_bars(self.config.lookback_days)
        df['spread_mean'] = df['spread'].rolling(window=lookback_bars).mean()
        df['spread_std'] = df['spread'].rolling(window=lookback_bars).std()
        df['zscore'] = (df['spread'] - df['spread_mean']) / df['spread_std']
        
        # 新增：計算 Z-Score 的動量（用於確認回歸趨勢）
        df['zscore_change'] = df['zscore'].diff()
        df['zscore_ema'] = df['zscore'].ewm(span=5).mean()  # 5 期 EMA 平滑 Z-Score
        
        # 計算價差的動量（ROC - Rate of Change）
        df['spread_roc'] = df['spread'].pct_change(5)  # 5 期報酬率
        
        # ATR
        df['atr_long'] = talib.ATR(df_long['high'], df_long['low'], df_long['close'], timeperiod=14)
        df['atr_short'] = talib.ATR(df_short['high'], df_short['low'], df_short['close'], timeperiod=14)
        
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna().reset_index(drop=True)
        
        return df
    
    def _days_to_bars(self, days):
        if self.config.timeframe == '15m':
            return days * 96
        elif self.config.timeframe == '1h':
            return days * 24
        elif self.config.timeframe == '4h':
            return days * 6
        else:
            return days * 24