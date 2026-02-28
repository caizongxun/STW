import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from .features import generate_features
from .labels import generate_labels
import joblib
import os
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

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
    
    if config.model_type == 'xgboost_lstm':
        # 构建LSTM模型
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(units=25))
        model.add(Dense(units=3, activation='softmax'))
        
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        
        # 调整数据形状
        X_train_lstm = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
        X_test_lstm = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)
        
        model.fit(X_train_lstm, y_train, batch_size=32, epochs=10)
    else:
        # 训练XGBoost模型
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
                             "models", f"{config.symbol}_{config.timeframe}_v6_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(model, os.path.join(model_dir, "model_0.pkl"))
    joblib.dump(config.__dict__, os.path.join(model_dir, "config.pkl"))
    joblib.dump(X.columns.tolist(), os.path.join(model_dir, "features.pkl"))
    
    return model, X, y