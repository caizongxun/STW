# 统一数据加载器(HuggingFace)
from datasets import load_dataset
import pandas as pd
import pyarrow as pa

class DataLoader:
    def __init__(self):
        self.dataset_name = "zongowo111/v2-crypto-ohlcv-data"
    
    def load_data(self, symbol="BTCUSDT", timeframe="15m"):
        # 加载HuggingFace数据集的default配置
        dataset = load_dataset(self.dataset_name, "default")
        df = pd.DataFrame(dataset["train"])
        
        # 筛选对应的交易对和时间框架
        df = df[(df["symbol"] == symbol) & (df["timeframe"] == timeframe)]
        
        # 转换时间格式
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
        
        return df