import pandas as pd
import numpy as np
import talib
from datetime import timedelta

class V9Backtester:
    """V9 趨勢回調狙擊手回測引擎"""
    
    def __init__(self, config):
        self.config = config
        
    def prepare_features(self, df):
        """生成技術指標"""
        df = df.copy()
        
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        
        df['ema_20'] = talib.EMA(df['close'], timeperiod=20)
        df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
        df['ema_200'] = talib.EMA(df['close'], timeperiod=200)
        
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        
        return df
    
    def run(self, df):
        print("[V9] Running Trend Pullback Sniper Strategy...")
        
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
                    # 平倉 50%
                    exit_price = tp1_price
                    partial_size = position_size_usd * self.config.partial_tp_pct
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = partial_size * pnl_pct - (partial_size * total_fee_rate * 2)
                    capital += pnl_usd
                    
                    # 移動止損到保本
                    sl_price = entry_price * 1.001
                    tp1_triggered = True
                    position_50 = position_size_usd - partial_size
                    tp1_count += 1
                    
                    print(f"[V9] TP1 觸發 @ {exit_price:.2f}, 平倉 {self.config.partial_tp_pct*100:.0f}%, 止損移到保本")
                
                # 檢查 TP2（剩餘倉位）
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
                    print(f"[V9] TP2 觸發 @ {exit_price:.2f}, 全部平倉")
                
                # 檢查止損
                elif row['low'] <= sl_price:
                    exit_price = sl_price
                    
                    if tp1_triggered:
                        # 保本止損
                        pnl_pct = (exit_price - entry_price) / entry_price
                        pnl_usd = position_50 * pnl_pct - (position_50 * total_fee_rate * 2)
                        capital += pnl_usd
                        breakeven_count += 1
                        print(f"[V9] 保本止損 @ {exit_price:.2f}")
                    else:
                        # 正常止損
                        pnl_pct = (exit_price - entry_price) / entry_price
                        pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                        capital += pnl_usd
                        sl_count += 1
                        print(f"[V9] 止損 @ {exit_price:.2f}")
                    
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
            # 2. 進場邏輯（放寬條件）
            # ==========================================
            if position == 0 and (i - last_exit_idx) >= self.config.cooldown_bars:
                if daily_trades_count >= self.config.max_daily_trades:
                    continue
                
                # 多頭趨勢（放寬：只要 EMA50 > EMA200）
                trend_up = row['ema_50'] > row['ema_200']
                if not trend_up:
                    continue
                
                # 價格回調到 EMA（放寬容忍度到 2%）
                pullback_ema = row['ema_50'] if self.config.pullback_to_ema == 'EMA50' else row['ema_20']
                near_ema = abs(row['close'] - pullback_ema) / row['close'] < 0.02
                if not near_ema:
                    continue
                
                # RSI 超賣（放寬到 40）
                if row['rsi'] > 40:
                    continue
                
                # 移除 MACD 過濾（太嚴格）
                # if row['macd_hist'] <= 0:
                #     continue
                
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
                
                print(f"[V9] 進場 @ {entry_price:.2f}, SL={sl_price:.2f}, TP1={tp1_price:.2f}, TP2={tp2_price:.2f}")
        
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
        
        print(f"[V9] 分批止盈統計: TP1={tp1_count}, TP2={tp2_count}, 保本={breakeven_count}, 止損={sl_count}")
        
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