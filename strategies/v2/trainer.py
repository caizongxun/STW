import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from .features import generate_features
from .labels import generate_labels
import joblib
import os
import pandas as pd

def train_model(data, config):
    # 生成特征和标签
    df = generate_features(data)
    y = generate_labels(df, config)
    
    # 准备数据
    X = df.drop(["open_time", "close_time", "open", "high", "low", "close", "volume", 
                 "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", 
                 "number_of_trades"], axis=1)
    
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    # 标准化
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # 训练模型
    model = xgb.XGBClassifier(
        objective="multi:softmax",
        num_class=3,
        max_depth=config.max_depth,
        learning_rate=0.1,
        n_estimators=100,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # 保存模型
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                             "models", f"{config.symbol}_{config.timeframe}_v1_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(model, os.path.join(model_dir, "model_0.pkl"))
    joblib.dump(config.__dict__, os.path.join(model_dir, "config.pkl"))
    joblib.dump(X.columns.tolist(), os.path.join(model_dir, "features.pkl"))
    
    return model, X, y