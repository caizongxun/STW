import pandas as pd
import numpy as np
import talib

class V3FeatureEngine:
    def __init__(self, config):
        self.config = config
        
    def generate(self, df):
        df = df.copy()
        
        # 1. 波動率指標 (Volatility)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['volatility_20'] = df['close'].pct_change().rolling(20).std()
        df['volatility_50'] = df['close'].pct_change().rolling(50).std()
        # 波動率斜率 (觀察波動率是在放大還是縮小)
        df['volatility_slope'] = df['volatility_20'] - df['volatility_20'].shift(5)
        
        # 2. 動量與趨勢類指標 (Momentum & Trend)
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        # RSI 差分，捕捉動能變化速度
        df['rsi_diff'] = df['rsi'].diff(3)
        
        macd, signal, hist = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist
        df['macd_hist_slope'] = df['macd_hist'].diff(2)
        
        # KDJ 指標
        df['slowk'], df['slowd'] = talib.STOCH(df['high'], df['low'], df['close'], fastk_period=9, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
        df['kdj_j'] = 3 * df['slowk'] - 2 * df['slowd']
        
        # ADX 趨勢強度
        df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
        
        # 3. 布林帶 (Bollinger Bands)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'], timeperiod=20)
        # BB 帶寬與收斂擴張
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        # 價格在布林帶的位置 (0~1)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-8)
        
        # 4. 成交量特徵 (Volume)
        vol_ma5 = df['volume'].rolling(5).mean()
        vol_ma20 = df['volume'].rolling(20).mean()
        df['vol_surge_5'] = (df['volume'] / (vol_ma5 + 1e-8)).clip(0, 5)
        df['vol_surge_20'] = (df['volume'] / (vol_ma20 + 1e-8)).clip(0, 5)
        # OBV
        df['obv'] = talib.OBV(df['close'], df['volume'])
        # OBV 動能
        df['obv_slope'] = df['obv'].pct_change(5)
        
        # 5. 多時間框架特徵 (模擬大一級別，如果是 15m 則模擬 1H)
        df['1h_sma20'] = df['close'].rolling(20 * 4).mean()
        df['1h_sma50'] = df['close'].rolling(50 * 4).mean()
        df['1h_trend'] = (df['1h_sma20'] > df['1h_sma50']).astype(int)
        
        # 6. K線形態特徵 (Price Action)
        body = abs(df['close'] - df['open'])
        total_range = df['high'] - df['low']
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
        
        # 影線比例
        df['lower_shadow_ratio'] = lower_shadow / (total_range + 1e-8)
        df['upper_shadow_ratio'] = upper_shadow / (total_range + 1e-8)
        df['body_ratio'] = body / (total_range + 1e-8)
        
        # 簡單判定：長下影線 (錘子線)
        df['is_hammer'] = ((lower_shadow > body * 2) & (upper_shadow < body * 0.3)).astype(int)
        # 頂部反轉：長上影線 (流星線)
        df['is_shooting_star'] = ((upper_shadow > body * 2) & (lower_shadow < body * 0.3)).astype(int)
        
        # 7. 價格統計特徵 (Statistical)
        # 過去 N 根 K 線的最高/最低價距離
        df['dist_from_high_20'] = (df['high'].rolling(20).max() - df['close']) / df['close']
        df['dist_from_low_20'] = (df['close'] - df['low'].rolling(20).min()) / df['close']
        
        # 清理無效值
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna()
        
        return df
        
    def get_feature_names(self, df):
        exclude = ['open', 'high', 'low', 'close', 'volume', 'open_time', 'close_time',
                   'label_long', 'label_short', 'label', 'target', 'barrier_hit', '1h_trend']
        return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]