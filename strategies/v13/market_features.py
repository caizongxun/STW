"""
市場特徵提取工具
將 K 線數據轉換為 AI 所需的 40+ 技術指標
修復: 添加 symbol 參數支持
"""
import pandas as pd
import talib


def prepare_market_features(row, df, symbol='UNKNOWN'):
    """
    將 DataFrame 的一行轉換為 DeepSeek 需要的格式（強化版：40+指標）
    
    Args:
        row: DataFrame 的一行數據
        df: 完整的 DataFrame
        symbol: 交易對符號 (例如 'BTCUSDT')
    
    Returns:
        dict: 包含所有市場特徵的字典
    """
    # 計算技術指標
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    
    # 趋勢
    ema9 = talib.EMA(close, timeperiod=9)
    ema21 = talib.EMA(close, timeperiod=21)
    ema50 = talib.EMA(close, timeperiod=50)
    ema200 = talib.EMA(close, timeperiod=200)
    macd, macd_signal, macd_hist = talib.MACD(close)
    adx = talib.ADX(high, low, close, timeperiod=14)
    
    # 動能
    rsi = talib.RSI(close, timeperiod=14)
    stoch_k, stoch_d = talib.STOCH(high, low, close)
    cci = talib.CCI(high, low, close, timeperiod=14)
    mfi = talib.MFI(high, low, close, volume, timeperiod=14)
    willr = talib.WILLR(high, low, close, timeperiod=14)
    
    # 波動
    atr = talib.ATR(high, low, close, timeperiod=14)
    bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20)
    
    # 成交量
    volume_ma = pd.Series(volume).rolling(20).mean().values
    obv = talib.OBV(close, volume)
    
    idx = len(df) - 1
    
    # 布林帶位置
    bb_pos = 0.5
    if bb_upper[idx] != bb_lower[idx]:
        bb_pos = (close[idx] - bb_lower[idx]) / (bb_upper[idx] - bb_lower[idx])
    
    # 成交量比率
    vol_ratio = volume[idx] / volume_ma[idx] if volume_ma[idx] > 0 else 1.0
    
    # 支擐/壓力
    pivot = (high[idx] + low[idx] + close[idx]) / 3
    resistance = pivot + (high[idx] - low[idx])
    support = pivot - (high[idx] - low[idx])
    
    return {
        'symbol': symbol,  # 使用傳入的 symbol 參數
        'close': float(row['close']),
        
        # 趋勢
        'ema9': float(ema9[idx]) if not pd.isna(ema9[idx]) else row['close'],
        'ema21': float(ema21[idx]) if not pd.isna(ema21[idx]) else row['close'],
        'ema50': float(ema50[idx]) if not pd.isna(ema50[idx]) else row['close'],
        'ema200': float(ema200[idx]) if not pd.isna(ema200[idx]) else row['close'],
        'macd': float(macd[idx]) if not pd.isna(macd[idx]) else 0,
        'macd_signal': float(macd_signal[idx]) if not pd.isna(macd_signal[idx]) else 0,
        'macd_hist': float(macd_hist[idx]) if not pd.isna(macd_hist[idx]) else 0,
        'adx': float(adx[idx]) if not pd.isna(adx[idx]) else 0,
        
        # 動能
        'rsi': float(rsi[idx]) if not pd.isna(rsi[idx]) else 50,
        'stoch_k': float(stoch_k[idx]) if not pd.isna(stoch_k[idx]) else 50,
        'stoch_d': float(stoch_d[idx]) if not pd.isna(stoch_d[idx]) else 50,
        'cci': float(cci[idx]) if not pd.isna(cci[idx]) else 0,
        'mfi': float(mfi[idx]) if not pd.isna(mfi[idx]) else 50,
        'willr': float(willr[idx]) if not pd.isna(willr[idx]) else -50,
        
        # 波動
        'atr': float(atr[idx]) if not pd.isna(atr[idx]) else row['close'] * 0.02,
        'bb_upper': float(bb_upper[idx]) if not pd.isna(bb_upper[idx]) else row['close'] * 1.02,
        'bb_middle': float(bb_middle[idx]) if not pd.isna(bb_middle[idx]) else row['close'],
        'bb_lower': float(bb_lower[idx]) if not pd.isna(bb_lower[idx]) else row['close'] * 0.98,
        'bb_position': float(bb_pos),
        
        # 成交量
        'volume_ratio': float(vol_ratio),
        'obv': float(obv[idx]) if not pd.isna(obv[idx]) else 0,
        
        # 支擐/壓力
        'dist_to_resistance': float((resistance - close[idx]) / close[idx] * 100),
        'dist_to_support': float((close[idx] - support) / close[idx] * 100)
    }
