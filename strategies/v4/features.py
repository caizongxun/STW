import pandas as pd
import numpy as np
import talib

class V4FeatureEngine:
    def __init__(self, config):
        self.config = config
        
    def generate(self, df):
        df = df.copy()
        
        # 1. 宏觀趨勢 (HTF Trend Filter)
        df['ema_trend'] = talib.EMA(df['close'], timeperiod=self.config.ema_trend)
        
        # 2. 波動率 (用於止損緩衝)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        
        # 3. ICT 核心：Fair Value Gap (FVG / 不平衡區間)
        # Bullish FVG: 第 1 根 K 線的 High 與 第 3 根 K 線的 Low 之間有缺口
        df['fvg_bull'] = df['low'] > df['high'].shift(2)
        df['fvg_bull_top'] = df['low']
        df['fvg_bull_bottom'] = df['high'].shift(2)
        
        # Bearish FVG: 第 1 根 K 線的 Low 與 第 3 根 K 線的 High 之間有缺口
        df['fvg_bear'] = df['high'] < df['low'].shift(2)
        df['fvg_bear_top'] = df['low'].shift(2)
        df['fvg_bear_bottom'] = df['high']
        
        # 清理並返回
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna().reset_index(drop=True)
        
        return df