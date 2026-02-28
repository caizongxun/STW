import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from .features import generate_features
from .labels import generate_labels
import joblib
import os
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam

def train_model(data, config):
    # 生成特征和标签
    df = generate_features(data)
    y = generate_labels(df, config)
    # 将标签转换为0,1,2，适配XGBoost的多分类要求
    y = y + 1
    
    # 准备数据
    feature_columns = [col for col in df.columns if col not in ["open_time", "close_time", "open", "high", "low", "close", "volume", 
                                                               "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", 
                                                               "number_of_trades"]]
    X = df[feature_columns]
    
    # 划分训练集和测试集（时间序列不能shuffle）
    train_size = int(0.8 * len(X))
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    # 标准化
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    if config.use_lstm:
        # LSTM模型需要的形状是 (samples, timesteps, features)
        timesteps = 1  # 单时间步
        features = X_train_scaled.shape[1]
        X_train_lstm = X_train_scaled.reshape((X_train_scaled.shape[0], timesteps, features))
        X_test_lstm = X_test_scaled.reshape((X_test_scaled.shape[0], timesteps, features))
        
        # 构建LSTM模型
        model = Sequential()
        model.add(LSTM(units=config.lstm_units, return_sequences=True, input_shape=(timesteps, features)))
        model.add(Dropout(config.dropout_rate))
        model.add(LSTM(units=config.lstm_units, return_sequences=False))
        model.add(Dropout(config.dropout_rate))
        model.add(Dense(units=25, activation='relu'))
        model.add(Dense(units=3, activation='softmax'))  # 3分类：1, -1, 0
        
        model.compile(optimizer=Adam(learning_rate=0.001),
                      loss='sparse_categorical_crossentropy',
                      metrics=['accuracy'])
        
        # 训练模型
        model.fit(X_train_lstm, y_train, batch_size=32, epochs=10, validation_data=(X_test_lstm, y_test))
    else:
        # XGBoost模型
        model = xgb.XGBClassifier(
            objective="multi:softmax",
            num_class=3,
            max_depth=config.max_depth,
            learning_rate=0.1,
            n_estimators=100,
            random_state=42,
            eval_metric="mlogloss"
        )
        model.fit(X_train_scaled, y_train, eval_set=[(X_test_scaled, y_test)], verbose=1)
    
    # 保存模型
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                             "models", f"{config.symbol}_{config.timeframe}_v6_{timestamp}")
    os.makedirs(model_dir, exist_ok=True)
    
    joblib.dump(model, os.path.join(model_dir, "model_0.pkl"))
    joblib.dump(config.__dict__, os.path.join(model_dir, "config.pkl"))
    joblib.dump(feature_columns, os.path.join(model_dir, "features.pkl"))
    joblib.dump(scaler, os.path.join(model_dir, "scaler.pkl"))
    
    return model, X, y, scaler