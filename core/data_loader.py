from datasets import load_dataset
import pandas as pd
import os

class DataLoader:
    def __init__(self):
        self.dataset_name = "zongowo111/v2-crypto-ohlcv-data"
        self.cache_dir = "data"
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def load_data(self, symbol="BTCUSDT", timeframe="15m"):
        cache_file = os.path.join(self.cache_dir, f"{symbol}_{timeframe}.parquet")
        
        # 1. 優先從本地緩存讀取
        if os.path.exists(cache_file):
            print(f"Loading {symbol} {timeframe} from local cache...")
            return pd.read_parquet(cache_file)
            
        print(f"Downloading {symbol} {timeframe}...")
        
        # 2. 避免使用 datasets.load_dataset，因為它會嘗試解析整個 repository 的結構
        # 直接使用 pandas 讀取 HuggingFace 的原始 parquet 檔案連結
        # 根據你之前截圖顯示的路徑結構: klines/BTCUSDT/BTC_15m.parquet
        try:
            base_symbol = symbol.replace("USDT", "")
            
            # Hugging Face raw file URL format
            # https://huggingface.co/datasets/zongowo111/v2-crypto-ohlcv-data/resolve/main/klines/BTCUSDT/BTC_15m.parquet
            url = f"https://huggingface.co/datasets/{self.dataset_name}/resolve/main/klines/{symbol}/{base_symbol}_{timeframe}.parquet"
            
            print(f"Fetching from direct URL: {url}")
            df = pd.read_parquet(url)
            
            # 轉換時間格式
            if "open_time" in df.columns:
                if pd.api.types.is_numeric_dtype(df["open_time"]):
                    if df["open_time"].iloc[0] > 1e11:
                        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
                    else:
                        df["open_time"] = pd.to_datetime(df["open_time"], unit="s")
                        
            if "close_time" in df.columns:
                if pd.api.types.is_numeric_dtype(df["close_time"]):
                    if df["close_time"].iloc[0] > 1e11:
                        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
                    else:
                        df["close_time"] = pd.to_datetime(df["close_time"], unit="s")
            
            # 存入本地緩存
            df.to_parquet(cache_file, index=False)
            print(f"Saved to {cache_file}")
            return df
            
        except Exception as e:
            print(f"Direct download failed: {e}")
            print("Falling back to HuggingFace datasets library...")
            
            # 3. 如果直接下載失敗，才用 datasets 庫 (這會觸發全部 meta 掃描)
            dataset = load_dataset(self.dataset_name, data_files=f"**/*{symbol}*_{timeframe}.parquet", split="train")
            df = pd.DataFrame(dataset)
            
            if "open_time" in df.columns and pd.api.types.is_numeric_dtype(df["open_time"]):
                df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            if "close_time" in df.columns and pd.api.types.is_numeric_dtype(df["close_time"]):
                df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
                
            df.to_parquet(cache_file, index=False)
            return df