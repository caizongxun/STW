import pandas as pd
import numpy as np
import talib
from datetime import timedelta
from core.llm_agent import DeepSeekTradingAgent

class V13Backtester:
    """V13 DeepSeek-R1 AI 回測引擎"""
    
    def __init__(self, config):
        self.config = config
        self.agent = DeepSeekTradingAgent()
        
    def prepare_features(self, df):
        """計算技術指標特徵"""
        df = df.copy()
        
        # 技術指標
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'])
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'], timeperiod=20)
        df['ema50'] = talib.EMA(df['close'], timeperiod=50)
        df['ema200'] = talib.EMA(df['close'], timeperiod=200)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        
        # 布林帶位置
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_position'] = df['bb_position'].clip(0, 1)
        
        # 成交量比率
        df['vol_ma'] = df['volume'].rolling(24).mean()
        df['volume_ratio'] = df['volume'] / df['vol_ma']
        
        df.dropna(inplace=True)
        return df
    
    def run(self, df):
        """執行回測"""
        try:
            if 'open_time' in df.columns:
                df['open_time'] = pd.to_datetime(df['open_time'])
            
            # 過濾時間範圍
            if self.config.simulation_days > 0:
                end_time = df['open_time'].max()
                start_time = end_time - timedelta(days=self.config.simulation_days)
                df = df[df['open_time'] >= start_time].reset_index(drop=True)
            
            # 準備技術指標
            df = self.prepare_features(df)
            
            if len(df) < 200:
                return {'error': '數據不足，至少需要 200 根 K 線'}
            
            # 初始化
            capital = self.config.capital
            initial_capital = capital
            peak_capital = capital
            
            position = 0
            entry_price = 0
            sl_price = 0
            tp_price = 0
            position_size_usd = 0
            entry_time = None
            entry_decision = None
            
            trades = []
            equity_curve = []
            ai_decisions = []  # 記錄所有 AI 決策
            
            trades_today = 0
            last_trade_date = None
            total_fee_rate = self.config.fee_rate + self.config.slippage
            
            real_start_time = df['open_time'].iloc[0]
            real_end_time = df['open_time'].iloc[-1]
            
            print(f"[V13] 開始回測 {self.config.symbol} ({self.config.timeframe})")
            print(f"[V13] 時間範圍: {real_start_time} ~ {real_end_time}")
            print(f"[V13] 總共 {len(df)} 根 K 線")
            
            # 每 N 根 K 線調用一次 AI（減少推理次數）
            decision_interval = 4  # 15m * 4 = 每小時決策一次
            
            for i in range(len(df)):
                row = df.iloc[i]
                equity_curve.append(capital)
                
                if capital > peak_capital:
                    peak_capital = capital
                if (peak_capital - capital) / peak_capital > self.config.max_drawdown_stop:
                    print(f"[V13] 觸發最大回撤停損 ({self.config.max_drawdown_stop*100}%)")
                    break
                
                current_date = row['open_time'].date()
                if current_date != last_trade_date:
                    trades_today = 0
                    last_trade_date = current_date
                
                # 1. 檢查出場
                if position == 1:
                    exit_price = 0
                    exit_reason = ''
                    
                    if row['high'] >= tp_price:
                        exit_price = tp_price
                        exit_reason = 'TP'
                    elif row['low'] <= sl_price:
                        exit_price = sl_price
                        exit_reason = 'SL'
                    
                    if exit_price > 0:
                        pnl_pct = (exit_price - entry_price) / entry_price
                        pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                        capital += pnl_usd
                        position = 0
                        
                        holding_hours = (row['open_time'] - entry_time).total_seconds() / 3600
                        
                        trade_record = {
                            'entry_time': entry_time,
                            'exit_time': row['open_time'],
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl_usd': pnl_usd,
                            'pnl_pct': pnl_pct,
                            'holding_hours': holding_hours,
                            'exit_reason': exit_reason
                        }
                        trades.append(trade_record)
                        
                        # 學習成功案例
                        if self.config.enable_learning and pnl_pct > self.config.min_profit_to_learn:
                            actual_result = {
                                'profit': pnl_usd,
                                'profit_percent': pnl_pct * 100,
                                'hold_hours': holding_hours
                            }
                            market_snapshot = self._extract_market_data(row)
                            self.agent.save_success_case(market_snapshot, entry_decision, actual_result)
                
                # 2. 進場邏輯（每 N 根 K 線調用 AI）
                if position == 0 and trades_today < self.config.max_daily_trades:
                    if i % decision_interval == 0:  # 降低 AI 調用頻率
                        market_data = self._extract_market_data(row)
                        
                        # 調用 DeepSeek-R1 進行決策
                        decision = self.agent.analyze_market(market_data)
                        ai_decisions.append(decision)
                        
                        # 只有當 AI 信心度足夠高時才開倉
                        if decision['signal'] in ['LONG', 'SHORT'] and \
                           decision.get('confidence', 0) >= self.config.ai_confidence_threshold * 100:
                            
                            if decision['signal'] == 'LONG':
                                position = 1
                                entry_price = row['close']
                                entry_time = row['open_time']
                                entry_decision = decision
                                
                                # 使用 AI 建議的止損與止盈
                                sl_price = decision['stop_loss']
                                tp_price = decision['take_profit']
                                
                                # 計算倉位大小
                                sl_distance = abs(entry_price - sl_price)
                                sl_pct = sl_distance / entry_price
                                max_loss = capital * self.config.base_risk
                                position_size_usd = min(max_loss / sl_pct, capital * self.config.max_leverage)
                                
                                trades_today += 1
            
            # 統計結算
            wins = len([t for t in trades if t['pnl_usd'] > 0])
            total = len(trades)
            win_rate = wins / total * 100 if total > 0 else 0
            total_return = (capital - initial_capital) / initial_capital * 100
            
            days_diff = (real_end_time - real_start_time).days
            monthly_return = total_return / (days_diff / 30.0) if days_diff > 0 else 0
            
            returns_series = pd.Series([t['pnl_pct'] for t in trades])
            sharpe_ratio = (returns_series.mean() / returns_series.std() * np.sqrt(252)) if len(returns_series) > 1 else 0
            
            total_profit = sum([t['pnl_usd'] for t in trades if t['pnl_usd'] > 0])
            total_loss = abs(sum([t['pnl_usd'] for t in trades if t['pnl_usd'] < 0]))
            profit_factor = total_profit / total_loss if total_loss > 0 else 0
            
            avg_holding_hours = np.mean([t['holding_hours'] for t in trades]) if trades else 0
            
            # AI 決策統計
            ai_signals_count = len([d for d in ai_decisions if d['signal'] != 'HOLD'])
            ai_avg_confidence = np.mean([d.get('confidence', 0) for d in ai_decisions if d['signal'] != 'HOLD'])
            execution_rate = (total / ai_signals_count * 100) if ai_signals_count > 0 else 0
            
            learned_cases = len(self.agent.success_cases)
            
            print(f"[V13] 回測完成！")
            print(f"[V13] 總報酬: {total_return:.2f}% | 勝率: {win_rate:.1f}% | 總交易: {total}")
            print(f"[V13] AI 信號數: {ai_signals_count} | 實際開倉: {total} | 執行率: {execution_rate:.1f}%")
            
            return {
                'final_capital': capital,
                'return_pct': total_return,
                'monthly_return': monthly_return,
                'total_trades': total,
                'win_rate': win_rate,
                'max_drawdown': self._calculate_max_drawdown(equity_curve),
                'days_tested': days_diff,
                'sharpe_ratio': sharpe_ratio,
                'profit_factor': profit_factor,
                'avg_holding_hours': avg_holding_hours,
                'equity_curve': equity_curve,
                'ai_signals_count': ai_signals_count,
                'ai_avg_confidence': ai_avg_confidence,
                'execution_rate': execution_rate,
                'learned_cases': learned_cases
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_market_data(self, row):
        """從 DataFrame row 提取市場數據"""
        return {
            'symbol': self.config.symbol,
            'close': float(row['close']),
            'rsi': float(row.get('rsi', 50)),
            'macd_hist': float(row.get('macd_hist', 0)),
            'bb_position': float(row.get('bb_position', 0.5)),
            'volume_ratio': float(row.get('volume_ratio', 1.0)),
            'ema50': float(row.get('ema50', row['close'])),
            'ema200': float(row.get('ema200', row['close'])),
            'atr': float(row.get('atr', row['close'] * 0.02))
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