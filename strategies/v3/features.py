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
    
    # 去除缺失值
    df = df.dropna()
    
    return df