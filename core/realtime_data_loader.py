"""
即時數據加載器 - 直接調用 Binance API
"""
import requests
import pandas as pd
from datetime import datetime


class RealtimeDataLoader:
    def __init__(self):
        self.base_url = "https://fapi.binance.com"  # Binance Futures API
    
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
            
            # Binance API endpoint
            url = f"{self.base_url}/fapi/v1/klines"
            
            params = {
                'symbol': symbol,
                'interval': timeframe,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                print(f"No data returned for {symbol} {timeframe}")
                return None
            
            # 轉換為 DataFrame
            # Binance klines format:
            # [open_time, open, high, low, close, volume, close_time, ...]
            df = pd.DataFrame(data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # 只保留需要的欄位
            df = df[['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time']]
            
            # 轉換時間格式 (Binance 使用毫秒)
            df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            # 確保數値類型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            print(f"Successfully loaded {len(df)} candles")
            print(f"Latest price: ${df['close'].iloc[-1]:,.2f}")
            print(f"Latest time: {df['timestamp'].iloc[-1]}")
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Network error loading realtime data: {e}")
            return None
        except Exception as e:
            print(f"Error loading realtime data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_latest_price(self, symbol="BTCUSDT"):
        """
        獲取最新價格
        """
        try:
            url = f"{self.base_url}/fapi/v1/ticker/price"
            params = {'symbol': symbol}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            return float(data['price'])
            
        except Exception as e:
            print(f"Error fetching latest price: {e}")
            return None
