import pandas as pd
import numpy as np
import talib

class V3FeatureEngine:
    def __init__(self, config):
        self.config = config
        
    def generate(self, df):
        df = df.copy()
        
        # 1. 波動率指標
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['volatility_20'] = df['close'].pct_change().rolling(20).std()
        
        # 2. 動量指標
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        macd, signal, hist = talib.MACD(df['close'])
        df['macd_hist'] = hist
        
        # 3. 宏觀趨勢指標 (順勢過濾器核心)
        df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
        df['ema_200'] = talib.EMA(df['close'], timeperiod=200)
        
        # 價格與均線的距離 (乖離率)
        df['dist_ema50'] = (df['close'] - df['ema_50']) / df['ema_50']
        df['dist_ema200'] = (df['close'] - df['ema_200']) / df['ema_200']
        
        # 4. 布林帶
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'], timeperiod=20)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-8)
        
        # 5. 成交量特徵
        vol_ma20 = df['volume'].rolling(20).mean()
        df['vol_surge_20'] = (df['volume'] / (vol_ma20 + 1e-8)).clip(0, 5)
        
        # 6. K線形態
        body = abs(df['close'] - df['open'])
        total_range = df['high'] - df['low']
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_shadow_ratio'] = lower_shadow / (total_range + 1e-8)
        df['upper_shadow_ratio'] = upper_shadow / (total_range + 1e-8)
        
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna()
        return df
        
    def get_feature_names(self, df):
        exclude = ['open', 'high', 'low', 'close', 'volume', 'open_time', 'close_time',
                   'label_long', 'label_short', 'label', 'target', 'barrier_hit']
        return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]