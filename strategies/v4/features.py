import pandas as pd
import numpy as np
import talib

class V4FeatureEngine:
    def __init__(self, config):
        self.config = config
        
    def generate(self, df):
        df = df.copy()
        
        # 1. 趨勢過濾：更嚴格的趨勢判定 (Fast > Slow 且 價格必須在 Fast 之上整理)
        df['ema_fast'] = talib.EMA(df['close'], timeperiod=self.config.ema_fast)
        df['ema_slow'] = talib.EMA(df['close'], timeperiod=self.config.ema_slow)
        
        # 判斷均線方向
        df['ema_fast_slope'] = df['ema_fast'].diff(3)
        df['ema_slow_slope'] = df['ema_slow'].diff(5)
        
        # 嚴格多頭：快慢線黃金交叉，且慢線向上，且快線也向上
        df['strict_uptrend'] = (df['ema_fast'] > df['ema_slow']) & (df['ema_slow_slope'] > 0) & (df['ema_fast_slope'] > 0)
        # 嚴格空頭
        df['strict_downtrend'] = (df['ema_fast'] < df['ema_slow']) & (df['ema_slow_slope'] < 0) & (df['ema_fast_slope'] < 0)
        
        # 2. 回踩判定 (SMC 中的 Order Block / FVGs 概念簡化)
        # 多頭回踩：價格回落到 EMA_fast 附近 (上下 0.5% 內)
        df['dist_to_fast_ema'] = abs(df['close'] - df['ema_fast']) / df['ema_fast']
        df['near_fast_ema'] = df['dist_to_fast_ema'] < 0.005
        
        df['rsi'] = talib.RSI(df['close'], timeperiod=self.config.rsi_period)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=self.config.atr_period)
        
        # 3. 價格行為：必須出現標誌性的 K 線 (Pin bar)
        body = abs(df['close'] - df['open'])
        total_range = df['high'] - df['low']
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
        
        # 嚴格的 Pin bar 定義 (影線極長，實體極小)
        df['strong_reject_lower'] = (lower_shadow > body * 2.0) & (lower_shadow > (total_range * 0.6))
        df['strong_reject_higher'] = (upper_shadow > body * 2.0) & (upper_shadow > (total_range * 0.6))
        
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna()
        return df