import talib
import pandas as pd
import numpy as np

def generate_features(data):
    df = data.copy()
    
    # 基础技术指标
    df["rsi"] = talib.RSI(df["close"], timeperiod=14)
    df["macd"], df["macdsignal"], df["macdhist"] = talib.MACD(df["close"])
    df["upper"], df["middle"], df["lower"] = talib.BBANDS(df["close"])
    df["atr"] = talib.ATR(df["high"], df["low"], df["close"], timeperiod=14)
    df["sma_20"] = talib.SMA(df["close"], timeperiod=20)
    df["sma_50"] = talib.SMA(df["close"], timeperiod=50)
    df["ema_20"] = talib.EMA(df["close"], timeperiod=20)
    df["ema_50"] = talib.EMA(df["close"], timeperiod=50)
    
    # 收益率特征
    df["return_1"] = df["close"].pct_change(1)
    df["return_5"] = df["close"].pct_change(5)
    df["return_20"] = df["close"].pct_change(20)
    
    # 波动率特征
    df["volatility_10"] = df["return_1"].rolling(10).std()
    df["volatility_20"] = df["return_1"].rolling(20).std()
    
    # 多时间框架特征
    # 1小时时间框架（15m*4=1h）
    df["1h_close"] = df["close"].rolling(4).mean()
    df["1h_rsi"] = talib.RSI(df["1h_close"], timeperiod=14)
    df["1h_sma_20"] = talib.SMA(df["1h_close"], timeperiod=20)
    df["1h_macd"], _, _ = talib.MACD(df["1h_close"])
    
    # 4小时时间框架（15m*16=4h）
    df["4h_close"] = df["close"].rolling(16).mean()
    df["4h_rsi"] = talib.RSI(df["4h_close"], timeperiod=14)
    df["4h_sma_50"] = talib.SMA(df["4h_close"], timeperiod=50)
    df["4h_atr"] = talib.ATR(df["high"].rolling(16).max(), df["low"].rolling(16).min(), df["4h_close"], timeperiod=14)
    
    # K线形态特征
    df["doji"] = np.where(abs(df["open"] - df["close"]) / (df["high"] - df["low"]) < 0.1, 1, 0)
    df["hammer"] = np.where((df["low"] == df["open"]) & (df["close"] - df["low"]) > (df["high"] - df["low"])*0.6, 1, 0)
    # 包容线形态
    df["engulfing"] = np.where(
        (df["close"] > df["open"]) & (df["open"] < df["close"].shift(1)) & (df["close"] > df["open"].shift(1)),
        1,
        np.where(
            (df["close"] < df["open"]) & (df["open"] > df["close"].shift(1)) & (df["close"] < df["open"].shift(1)),
            -1,
            0
        )
    )
    
    # 成交量特征
    df["volume_spike"] = np.where(df["volume"] > df["volume"].rolling(20).mean() * 2, 1, 0)
    df["volume_trend"] = np.where(df["volume"].rolling(5).mean() > df["volume"].rolling(20).mean(), 1, -1)
    # 价量配合
    df["volume_price_correlation"] = df["return_1"].rolling(10).corr(df["volume"].pct_change(1))
    
    # 去除缺失值
    df = df.dropna()
    
    return df