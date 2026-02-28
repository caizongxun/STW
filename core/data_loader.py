# 统一数据加载器(HuggingFace)
from datasets import load_dataset
import pandas as pd
import pyarrow as pa

class DataLoader:
    def __init__(self):
        self.dataset_name = "zongowo111/v2-crypto-ohlcv-data"
    
    def load_data(self, symbol="BTCUSDT", timeframe="15m"):
        # 加载HuggingFace数据集
        dataset = load_dataset(self.dataset_name, f"{symbol}_{timeframe}")
        df = pd.DataFrame(dataset["train"])
        
        # 转换时间格式
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
        
        return df