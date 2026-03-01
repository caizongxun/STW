import pandas as pd
import numpy as np
import talib

class V3FeatureEngine:
    def __init__(self, config):
        self.config = config
        
    def generate(self, df):
        df = df.copy()
        
        # 1. 波動率指標 (Triple Barrier 必備)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['volatility_20'] = df['close'].pct_change().rolling(20).std()
        
        # 2. 動量與趨勢類指標
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        macd, signal, hist = talib.MACD(df['close'])
        df['macd'] = macd
        df['macd_hist'] = hist
        
        # 3. 布林帶 (超買超賣極端值)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'], timeperiod=20)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-8)
        
        # 4. 成交量特徵
        vol_ma5 = df['volume'].rolling(5).mean()
        df['vol_surge'] = (df['volume'] / (vol_ma5 + 1e-8)).clip(0, 5)
        
        # 5. 多時間框架特徵 (模擬)
        # 1h = 4 * 15m
        df['1h_sma20'] = df['close'].rolling(20 * 4).mean()
        df['1h_sma50'] = df['close'].rolling(50 * 4).mean()
        df['1h_rsi'] = talib.RSI(df['close'].iloc[::4].reindex(df.index, method='ffill'), timeperiod=14)
        
        # 6. 反轉形態特徵
        # 簡單判定：長下影線 (錘子線)
        body = abs(df['close'] - df['open'])
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
        df['is_hammer'] = ((lower_shadow > body * 2) & (upper_shadow < body * 0.3)).astype(int)
        
        # 頂部反轉：長上影線 (流星線/倒錘子)
        df['is_shooting_star'] = ((upper_shadow > body * 2) & (lower_shadow < body * 0.3)).astype(int)
        
        df = df.dropna()
        return df
        
    def get_feature_names(self, df):
        exclude = ['open', 'high', 'low', 'close', 'volume', 'open_time', 'close_time',
                   'label_long', 'label_short', 'label', 'target', 'barrier_hit']
        return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]