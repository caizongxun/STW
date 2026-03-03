import pandas as pd
import numpy as np
import talib
from datetime import timedelta

class V10Backtester:
    """V10 波動爆發狙擊手回測引擎"""
    
    def __init__(self, config):
        self.config = config
        
    def prepare_features(self, df):
        df = df.copy()
        
        # 基礎指標
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        
        # 趨勢與出場均線
        df['ema_9'] = talib.EMA(df['close'], timeperiod=9)     # 動態出場線
        df['ema_50'] = talib.EMA(df['close'], timeperiod=50)   # 趨勢判定
        df['ema_200'] = talib.EMA(df['close'], timeperiod=200) # 大趨勢判定
        
        # Bollinger Bands (布林帶)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'], timeperiod=20, nbdevup=2, nbdevdn=2
        )
        
        # 帶寬 (Band Width) 與擠壓判定
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        # 計算過去 N 根 K 線的平均帶寬
        df['bb_width_ma'] = df['bb_width'].rolling(self.config.squeeze_length).mean()
        
        # 擠壓條件：當前帶寬低於平均帶寬 (代表市場極度平靜)
        df['is_squeeze'] = df['bb_width'] < df['bb_width_ma']
        
        # 成交量均線
        df['volume_ma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma'].replace(0, 0.0001)
        
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        return df
    
    def run(self, df):
        print(f"[V10] Running BB Squeeze Breakout Strategy...")
        
        df = self.prepare_features(df)
        
        if 'open_time' in df.columns:
            df['open_time'] = pd.to_datetime(df['open_time'])
        
        if self.config.simulation_days > 0:
            end_time = df['open_time'].max()
            start_time = end_time - timedelta(days=self.config.simulation_days)
            df = df[df['open_time'] >= start_time].reset_index(drop=True)
        
        capital = self.config.capital
        initial_capital = capital
        peak_capital = capital
        
        position = 0
        entry_price = 0
        sl_price = 0
        tp_price = 0
        position_size_usd = 0
        entry_time = None
        
        trades = []
        equity_curve = []
        last_exit_idx = -self.config.cooldown_bars
        total_fee_rate = self.config.fee_rate + self.config.slippage
        
        for i in range(50, len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            if capital > peak_capital:
                peak_capital = capital
            if (peak_capital - capital) / peak_capital > self.config.max_drawdown_stop:
                break
            
            # ==========================================
            # 1. 倉位管理與出場邏輯
            # ==========================================
            if position == 1:
                exit_price = 0
                reason = ""
                
                # 檢查固定止損 (任何模式都有效)
                if row['low'] <= sl_price:
                    exit_price = sl_price
                    reason = "sl"
                
                # 模式 A: 固定盈虧比
                elif self.config.exit_mode == 'fixed_rr' and row['high'] >= tp_price:
                    exit_price = tp_price
                    reason = "tp"
                
                # 模式 B: EMA9 追蹤出場 (當收盤價跌破 EMA9 時出場)
                elif self.config.exit_mode == 'ema_trailing':
                    # 如果收盤價低於 EMA9，且我們已經獲利(避免剛進場就被小波動洗掉)
                    if row['close'] < row['ema_9'] and row['close'] > entry_price * 1.005:
                        exit_price = row['close']
                        reason = "ema_trailing_profit"
                
                # 執行出場
                if exit_price > 0:
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    
                    position = 0
                    holding_hours = (row['open_time'] - entry_time).total_seconds() / 3600 if entry_time else 0
                    trades.append({
                        'pnl_usd': pnl_usd, 
                        'return': pnl_pct, 
                        'holding_hours': holding_hours,
                        'reason': reason
                    })
                    last_exit_idx = i
            
            # ==========================================
            # 2. 進場邏輯 (波動爆發狙擊)
            # ==========================================
            if position == 0 and (i - last_exit_idx) >= self.config.cooldown_bars:
                
                # 條件 1：大趨勢必須為多頭 (避免逆勢做多)
                if row['ema_50'] <= row['ema_200']:
                    continue
                
                # 條件 2：前一根K線處於「擠壓」狀態 (市場平靜)
                prev_row = df.iloc[i-1]
                if not prev_row['is_squeeze']:
                    continue
                
                # 條件 3：當前K線強勢突破布林帶上軌
                is_breakout = row['close'] > row['bb_upper']
                if not is_breakout:
                    continue
                
                # 條件 4：強烈動能確認 (RSI > 設定值)
                if row['rsi'] < self.config.rsi_momentum:
                    continue
                
                # 條件 5：成交量放大 (機構資金參與)
                if row['volume_ratio'] < self.config.volume_surge:
                    continue
                
                # 執行進場
                position = 1
                entry_price = row['close']
                entry_time = row['open_time'] if 'open_time' in df.columns else None
                
                # 止損設在布林帶中軌 (EMA20)，因為跌破中軌代表突破失敗
                sl_price = row['bb_middle']
                
                # 安全機制：確保止損距離不會過大或過小
                sl_distance = entry_price - sl_price
                min_sl = entry_price * 0.005  # 至少 0.5%
                max_sl = entry_price * 0.03   # 最多 3.0%
                
                if sl_distance < min_sl: sl_price = entry_price - min_sl
                if sl_distance > max_sl: sl_price = entry_price - max_sl
                
                sl_pct = (entry_price - sl_price) / entry_price
                
                if self.config.exit_mode == 'fixed_rr':
                    tp_price = entry_price + (entry_price - sl_price) * self.config.tp_r
                
                # 資金管理
                max_loss = capital * self.config.base_risk
                position_size_usd = min(max_loss / sl_pct, capital * self.config.max_leverage)
        
        # 結算
        wins = len([t for t in trades if t['pnl_usd'] > 0])
        total = len(trades)
        win_rate = wins / total if total > 0 else 0
        total_return = (capital - initial_capital) / initial_capital * 100
        
        days_diff = (end_time - start_time).days if start_time and end_time else 0
        monthly_return = total_return / (days_diff / 30.0) if days_diff > 0 else 0
        
        returns_series = pd.Series([t['return'] for t in trades])
        sharpe_ratio = (returns_series.mean() / returns_series.std() * np.sqrt(252)) if len(returns_series) > 1 else 0
        
        total_profit = sum([t['pnl_usd'] for t in trades if t['pnl_usd'] > 0])
        total_loss = abs(sum([t['pnl_usd'] for t in trades if t['pnl_usd'] < 0]))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        avg_holding_hours = np.mean([t['holding_hours'] for t in trades]) if trades else 0
        
        return {
            'final_capital': capital,
            'return_pct': total_return,
            'monthly_return': monthly_return,
            'total_trades': total,
            'win_rate': win_rate * 100,
            'max_drawdown': self._calculate_max_drawdown(equity_curve),
            'days_tested': days_diff,
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': profit_factor,
            'avg_holding_hours': avg_holding_hours
        }
    
    def _calculate_max_drawdown(self, equity_curve):
        if not equity_curve: return 0.0
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak: peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd: max_dd = dd
        return max_dd