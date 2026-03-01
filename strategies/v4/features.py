import pandas as pd
import numpy as np
import talib

class V4FeatureEngine:
    def __init__(self, config):
        self.config = config
        
    def generate(self, df):
        df = df.copy()
        
        # 1. 趨勢與波動率
        df['ema_trend'] = talib.EMA(df['close'], timeperiod=self.config.ema_trend)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        
        # 2. 流動性掠奪 (Liquidity Sweep) 偵測
        # 計算過去 N 根 K 線的最高與最低點 (不含當前 K 線)
        df['swing_high'] = df['high'].shift(1).rolling(self.config.sweep_lookback).max()
        df['swing_low'] = df['low'].shift(1).rolling(self.config.sweep_lookback).min()
        
        # Sweep: 價格戳破前高/前低，但收盤收回來
        # 戳破前低，收盤拉回 (看漲的流動性掠奪)
        df['sweep_low'] = (df['low'] < df['swing_low']) & (df['close'] > df['swing_low'])
        # 戳破前高，收盤跌回 (看跌的流動性掠奪)
        df['sweep_high'] = (df['high'] > df['swing_high']) & (df['close'] < df['swing_high'])
        
        # 3. 高質量 FVG 偵測
        # Bullish FVG
        fvg_bull_condition = df['low'] > df['high'].shift(2)
        fvg_bull_size = df['low'] - df['high'].shift(2)
        # 過濾掉微小無意義的缺口
        df['fvg_bull'] = fvg_bull_condition & (fvg_bull_size > (df['atr'] * self.config.fvg_min_size_atr))
        df['fvg_bull_top'] = df['low']
        df['fvg_bull_bottom'] = df['high'].shift(2)
        
        # Bearish FVG
        fvg_bear_condition = df['high'] < df['low'].shift(2)
        fvg_bear_size = df['low'].shift(2) - df['high']
        df['fvg_bear'] = fvg_bear_condition & (fvg_bear_size > (df['atr'] * self.config.fvg_min_size_atr))
        df['fvg_bear_top'] = df['low'].shift(2)
        df['fvg_bear_bottom'] = df['high']
        
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna().reset_index(drop=True)
        
        return df