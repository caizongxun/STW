import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from .features import V3FeatureEngine
from .labels import V3LabelGenerator

class V3Trainer:
    def __init__(self, config):
        self.config = config
        self.long_model = None
        self.short_model = None
        self.feature_names = []
        
    def train(self, df):
        print("[V3 Triple Barrier Strategy Training]")
        
        fe = V3FeatureEngine(self.config)
        df = fe.generate(df)
        
        lg = V3LabelGenerator(self.config)
        df = lg.generate(df)
        
        self.feature_names = fe.get_feature_names(df)
        X = df[self.feature_names]
        
        valid = df['label_long'].notna()
        X = X[valid]
        y_long = df['label_long'][valid]
        y_short = df['label_short'][valid]
        
        # 避免未來函數，採時間序列切分
        train_size = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
        yl_train, yl_test = y_long.iloc[:train_size], y_long.iloc[train_size:]
        ys_train, ys_test = y_short.iloc[:train_size], y_short.iloc[train_size:]
        
        print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
        print(f"Long samples: {yl_train.sum()} ({yl_train.sum()/len(yl_train)*100:.1f}%)")
        print(f"Short samples: {ys_train.sum()} ({ys_train.sum()/len(ys_train)*100:.1f}%)")
        
        # 處理極端不平衡，如果沒有正樣本則設為1
        long_weight = (len(yl_train) - yl_train.sum()) / max(1, yl_train.sum())
        short_weight = (len(ys_train) - ys_train.sum()) / max(1, ys_train.sum())
        
        params = {
            'objective': 'binary',
            'num_leaves': self.config.num_leaves,
            'learning_rate': self.config.learning_rate,
            'max_depth': self.config.max_depth,
            'reg_alpha': self.config.reg_alpha,
            'n_estimators': self.config.n_estimators,
            'verbose': -1,
            'random_state': 42
        }
        
        # Train Long
        print("Training Long Model...")
        self.long_model = lgb.LGBMClassifier(**params, scale_pos_weight=long_weight)
        self.long_model.fit(X_train, yl_train)
        
        # Train Short
        print("Training Short Model...")
        self.short_model = lgb.LGBMClassifier(**params, scale_pos_weight=short_weight)
        self.short_model.fit(X_train, ys_train)
        
        # Eval
        long_prob = self.long_model.predict_proba(X_test)[:, 1]
        short_prob = self.short_model.predict_proba(X_test)[:, 1]
        
        long_pred = (long_prob > self.config.signal_threshold).astype(int)
        short_pred = (short_prob > self.config.signal_threshold).astype(int)
        
        results = {
            'long_metrics': {
                'auc': float(roc_auc_score(yl_test, long_prob)),
                'precision': float(precision_score(yl_test, long_pred, zero_division=0)),
                'recall': float(recall_score(yl_test, long_pred, zero_division=0))
            },
            'short_metrics': {
                'auc': float(roc_auc_score(ys_test, short_prob)),
                'precision': float(precision_score(ys_test, short_pred, zero_division=0)),
                'recall': float(recall_score(ys_test, short_pred, zero_division=0))
            }
        }
        
        return results