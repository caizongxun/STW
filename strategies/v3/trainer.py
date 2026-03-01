import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from .features import V3FeatureEngine
from .labels import V3LabelGenerator
from imblearn.over_sampling import SMOTE

class V3Trainer:
    def __init__(self, config):
        self.config = config
        self.long_model = None
        self.short_model = None
        self.feature_names = []
        
    def train(self, df):
        print("[V3 Triple Barrier Strategy Training - Optimized]")
        
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
        
        train_size = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
        yl_train, yl_test = y_long.iloc[:train_size], y_long.iloc[train_size:]
        ys_train, ys_test = y_short.iloc[:train_size], y_short.iloc[train_size:]
        
        print(f"Original Long samples: {yl_train.sum()} ({yl_train.sum()/len(yl_train)*100:.1f}%)")
        print(f"Original Short samples: {ys_train.sum()} ({ys_train.sum()/len(ys_train)*100:.1f}%)")
        
        # 使用 SMOTE 解決嚴重樣本不平衡問題
        try:
            smote = SMOTE(random_state=42)
            X_train_long_sm, yl_train_sm = smote.fit_resample(X_train, yl_train)
            X_train_short_sm, ys_train_sm = smote.fit_resample(X_train, ys_train)
            print(f"After SMOTE Long samples: {yl_train_sm.sum()}")
            print(f"After SMOTE Short samples: {ys_train_sm.sum()}")
        except Exception as e:
            print(f"SMOTE failed (possibly too few samples): {e}")
            X_train_long_sm, yl_train_sm = X_train, yl_train
            X_train_short_sm, ys_train_sm = X_train, ys_train
        
        # 調整模型超參數 (防過擬合與增強捕捉能力)
        params = {
            'objective': 'binary',
            'metric': 'auc',
            'num_leaves': 31,
            'learning_rate': 0.03,
            'max_depth': 6,
            'min_child_samples': 20,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'reg_alpha': 0.5,
            'reg_lambda': 0.5,
            'n_estimators': 150,
            'class_weight': 'balanced', # 進一步強調平衡
            'verbose': -1,
            'random_state': 42
        }
        
        print("Training Long Model...")
        self.long_model = lgb.LGBMClassifier(**params)
        self.long_model.fit(X_train_long_sm, yl_train_sm)
        
        print("Training Short Model...")
        self.short_model = lgb.LGBMClassifier(**params)
        self.short_model.fit(X_train_short_sm, ys_train_sm)
        
        # Eval
        long_prob = self.long_model.predict_proba(X_test)[:, 1]
        short_prob = self.short_model.predict_proba(X_test)[:, 1]
        
        # 放寬預測閾值以提升 Recall
        pred_threshold = 0.55
        
        long_pred = (long_prob > pred_threshold).astype(int)
        short_pred = (short_prob > pred_threshold).astype(int)
        
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