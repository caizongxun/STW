"""
即時數據加載器 - 使用 Binance API 獲取最新價格
"""
import ccxt
import pandas as pd
from datetime import datetime, timedelta


class RealtimeDataLoader:
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'  # 使用合約
            }
        })
    
    def load_data(self, symbol="BTCUSDT", timeframe="15m", limit=500):
        """
        獲取即時 OHLCV 數據
        
        Args:
            symbol: 交易對，例如 "BTCUSDT"
            timeframe: K 線周期，例如 "15m", "1h", "4h"
            limit: 獲取數量，預設 500
        
        Returns:
            pd.DataFrame: 包含 timestamp, open, high, low, close, volume
        """
        try:
            print(f"Fetching realtime data for {symbol} {timeframe}...")
            
            # 獲取 OHLCV 數據
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit
            )
            
            if not ohlcv:
                print(f"No data returned for {symbol} {timeframe}")
                return None
            
            # 轉換為 DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # 轉換時間格式
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open_time'] = df['timestamp']
            df['close_time'] = df['timestamp'] + pd.Timedelta(minutes=self._get_timeframe_minutes(timeframe))
            
            # 確保數値類型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            print(f"Successfully loaded {len(df)} candles")
            print(f"Latest price: ${df['close'].iloc[-1]:,.2f}")
            print(f"Latest time: {df['timestamp'].iloc[-1]}")
            
            return df
            
        except Exception as e:
            print(f"Error loading realtime data: {e}")
            return None
    
    def get_latest_price(self, symbol="BTCUSDT"):
        """
        獲取最新價格
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error fetching latest price: {e}")
            return None
    
    def _get_timeframe_minutes(self, timeframe):
        """
        將 timeframe 轉換為分鐘數
        """
        timeframe_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }
        return timeframe_map.get(timeframe, 15)
