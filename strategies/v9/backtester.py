import pandas as pd
import numpy as np
import talib
from datetime import timedelta

class V9Backtester:
    """V9 趨勢回調狙擊手回測引擎 - 動態超賣確認"""
    
    def __init__(self, config):
        self.config = config
        
    def prepare_features(self, df):
        """生成進階技術指標"""
        df = df.copy()
        
        # 基礎指標
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        
        # EMA 趨勢
        df['ema_20'] = talib.EMA(df['close'], timeperiod=20)
        df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
        df['ema_200'] = talib.EMA(df['close'], timeperiod=200)
        
        # 布林帶
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'], timeperiod=20, nbdevup=2, nbdevdn=2
        )
        
        # BB%B - 價格在布林帶中的位置（0-1）
        bb_width = df['bb_upper'] - df['bb_lower']
        df['bb_position'] = (df['close'] - df['bb_lower']) / bb_width.replace(0, 0.0001)
        
        # Z-Score - 價格偏離均值的標準差數
        ma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        df['z_score'] = (df['close'] - ma_20) / std_20.replace(0, 0.0001)
        
        # Stochastic RSI - 更靈敏的 RSI
        rsi_14_low = df['rsi'].rolling(14).min()
        rsi_14_high = df['rsi'].rolling(14).max()
        rsi_range = rsi_14_high - rsi_14_low
        df['stoch_rsi'] = (df['rsi'] - rsi_14_low) / rsi_range.replace(0, 0.0001)
        
        # 成交量確認
        df['volume_ma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma'].replace(0, 0.0001)
        
        # ATR 百分位（用於動態調整閾值）
        df['atr_ma'] = df['atr'].rolling(50).mean()
        df['atr_percentile'] = df['atr'] / df['atr_ma'].replace(0, 0.0001)
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        
        return df
    
    def run(self, df):
        print("[V9] Running Trend Pullback Sniper Strategy with Dynamic Indicators...")
        
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
        position_50 = 0
        entry_price = 0
        sl_price = 0
        tp1_price = 0
        tp2_price = 0
        position_size_usd = 0
        entry_time = None
        tp1_triggered = False
        
        trades = []
        equity_curve = []
        daily_trades_count = 0
        last_trade_date = None
        last_exit_idx = -self.config.cooldown_bars
        
        start_time = df['open_time'].iloc[0] if 'open_time' in df.columns else None
        end_time = df['open_time'].iloc[-1] if 'open_time' in df.columns else None
        
        total_fee_rate = self.config.fee_rate + self.config.slippage
        
        tp1_count = 0
        tp2_count = 0
        breakeven_count = 0
        sl_count = 0
        entry_signal_count = 0
        
        for i in range(200, len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            if capital > peak_capital:
                peak_capital = capital
            
            current_dd = (peak_capital - capital) / peak_capital
            if current_dd > self.config.max_drawdown_stop:
                print(f"[V9] 回撤超過 {self.config.max_drawdown_stop*100}%，停止交易")
                break
            
            if 'open_time' in df.columns:
                current_date = row['open_time'].date()
                if last_trade_date != current_date:
                    daily_trades_count = 0
                    last_trade_date = current_date
            
            # ==========================================
            # 1. 倉位管理（分批止盈）
            # ==========================================
            if position != 0:
                # 檢查 TP1
                if not tp1_triggered and row['high'] >= tp1_price:
                    exit_price = tp1_price
                    partial_size = position_size_usd * self.config.partial_tp_pct
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = partial_size * pnl_pct - (partial_size * total_fee_rate * 2)
                    capital += pnl_usd
                    
                    # 移動止損到保本
                    sl_price = entry_price * 1.002
                    tp1_triggered = True
                    position_50 = position_size_usd - partial_size
                    tp1_count += 1
                
                # 檢查 TP2
                if tp1_triggered and row['high'] >= tp2_price:
                    exit_price = tp2_price
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_50 * pnl_pct - (position_50 * total_fee_rate * 2)
                    capital += pnl_usd
                    
                    position = 0
                    position_50 = 0
                    tp1_triggered = False
                    last_exit_idx = i
                    tp2_count += 1
                    
                    holding_hours = (row['open_time'] - entry_time).total_seconds() / 3600 if entry_time else 0
                    trades.append({
                        'type': 'tp2',
                        'pnl_usd': pnl_usd,
                        'return': pnl_pct,
                        'capital': capital,
                        'holding_hours': holding_hours
                    })
                
                # 檢查止損
                elif row['low'] <= sl_price:
                    exit_price = sl_price
                    
                    if tp1_triggered:
                        pnl_pct = (exit_price - entry_price) / entry_price
                        pnl_usd = position_50 * pnl_pct - (position_50 * total_fee_rate * 2)
                        capital += pnl_usd
                        breakeven_count += 1
                    else:
                        pnl_pct = (exit_price - entry_price) / entry_price
                        pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                        capital += pnl_usd
                        sl_count += 1
                    
                    position = 0
                    position_50 = 0
                    tp1_triggered = False
                    last_exit_idx = i
                    
                    holding_hours = (row['open_time'] - entry_time).total_seconds() / 3600 if entry_time else 0
                    trades.append({
                        'type': 'sl',
                        'pnl_usd': pnl_usd,
                        'return': pnl_pct,
                        'capital': capital,
                        'holding_hours': holding_hours
                    })
            
            # ==========================================
            # 2. 進場邏輯（放寬過濾器）
            # ==========================================
            if position == 0 and (i - last_exit_idx) >= self.config.cooldown_bars:
                if daily_trades_count >= self.config.max_daily_trades:
                    continue
                
                # 條件 1：多頭趨勢
                trend_up = (row['ema_50'] > row['ema_200']) and (row['close'] > row['ema_200'])
                if not trend_up:
                    continue
                
                # 條件 2：價格回調到 EMA50 附近 (放寬從 2.5% 到 4.0%)
                pullback_ema = row['ema_50']
                near_ema = abs(row['close'] - pullback_ema) / row['close'] < 0.040
                if not near_ema:
                    continue
                
                # 條件 3：動態超賣確認（放寬，至少滿足 1 個即可，之前是 2 個）
                if row['atr_percentile'] > 1.3:  # 高波動
                    z_threshold = -1.0
                    bb_threshold = 0.35
                    stoch_threshold = 0.40
                else:  # 低波動
                    z_threshold = -1.5
                    bb_threshold = 0.30
                    stoch_threshold = 0.30
                
                oversold_signals = [
                    row['z_score'] < z_threshold,           
                    row['bb_position'] < bb_threshold,      
                    row['stoch_rsi'] < stoch_threshold      
                ]
                
                if sum(oversold_signals) < 1:  # 放寬！
                    continue
                
                entry_signal_count += 1
                
                # 取消成交量過濾器 (這往往會錯殺好機會)
                # if row['volume_ratio'] < 0.8:
                #     continue
                
                # 條件 5：MACD 開始轉強
                macd_turning = row['macd_hist'] > df['macd_hist'].iloc[i-1]
                if not macd_turning:
                    continue
                
                # 開倉
                position = 1
                entry_price = row['close']
                entry_time = row['open_time'] if 'open_time' in df.columns else None
                
                sl_distance = row['atr'] * self.config.atr_multiplier
                sl_price = entry_price - sl_distance
                tp1_price = entry_price + sl_distance * self.config.tp1_r
                tp2_price = entry_price + sl_distance * self.config.tp2_r
                
                sl_pct = sl_distance / entry_price
                max_loss = capital * self.config.base_risk
                position_size_usd = min(max_loss / sl_pct, capital * self.config.max_leverage)
                
                daily_trades_count += 1
                tp1_triggered = False
        
        # 統計
        wins = len([t for t in trades if t['pnl_usd'] > 0])
        total = len(trades)
        win_rate = wins / total if total > 0 else 0
        total_return = (capital - initial_capital) / initial_capital * 100
        
        days_diff = 0
        monthly_return = 0
        if start_time and end_time:
            days_diff = (end_time - start_time).days
            if days_diff > 0:
                monthly_return = total_return / (days_diff / 30.0)
        
        returns_series = pd.Series([t['return'] for t in trades])
        sharpe_ratio = (returns_series.mean() / returns_series.std() * np.sqrt(252)) if len(returns_series) > 1 else 0
        
        total_profit = sum([t['pnl_usd'] for t in trades if t['pnl_usd'] > 0])
        total_loss = abs(sum([t['pnl_usd'] for t in trades if t['pnl_usd'] < 0]))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        avg_holding_hours = np.mean([t['holding_hours'] for t in trades if 'holding_hours' in t]) if trades else 0
        
        print(f"[V9] 信號統計: 符合進場條件={entry_signal_count}, 實際交易={total}")
        print(f"[V9] 分批止盈: TP1={tp1_count}, TP2={tp2_count}, 保本={breakeven_count}, 止損={sl_count}")
        
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
            'avg_holding_hours': avg_holding_hours,
            'partial_tp_stats': {
                'tp1_count': tp1_count,
                'tp2_count': tp2_count,
                'breakeven_count': breakeven_count,
                'sl_count': sl_count
            }
        }
    
    def _calculate_max_drawdown(self, equity_curve):
        if not equity_curve:
            return 0.0
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return max_dd