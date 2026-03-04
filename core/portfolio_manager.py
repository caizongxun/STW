"""
倉位管理器
管理持倉、資金、交易歷史，為AI提供倉位上下文
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import uuid


class PortfolioManager:
    """管理交易帳戶狀態與持倉記錄"""
    
    def __init__(self, initial_capital: float = 10000, state_file: str = "data/portfolio_state.json"):
        self.state_file = Path(state_file)
        self.initial_capital = initial_capital
        self.load_state()
    
    def load_state(self):
        """從文件載入當前狀態"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                self.capital = state.get('capital', self.initial_capital)
                self.positions = state.get('positions', [])
                self.trade_history = state.get('trade_history', [])
                self.statistics = state.get('statistics', {})
                print(f"Loaded portfolio state: ${self.capital:.2f}, {len(self.positions)} positions")
        else:
            self.capital = self.initial_capital
            self.positions = []
            self.trade_history = []
            self.statistics = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'max_drawdown': 0.0,
                'consecutive_losses': 0,
                'consecutive_wins': 0
            }
            print(f"Initialized new portfolio with ${self.initial_capital:.2f}")
    
    def save_state(self):
        """保存當前狀態到文件"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            'capital': self.capital,
            'positions': self.positions,
            'trade_history': self.trade_history,
            'statistics': self.statistics,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def get_current_context(self, current_prices: Dict[str, float] = None) -> Dict:
        """
        生成給AI的倉位上下文
        
        Args:
            current_prices: {'BTCUSDT': 65000, 'ETHUSDT': 3500, ...}
        
        Returns:
            包含倉位、資金、歷史統計的字典
        """
        current_prices = current_prices or {}
        
        # 計算持倉詳情
        positions_detail = []
        total_position_value = 0
        
        for pos in self.positions:
            current_price = current_prices.get(pos['symbol'], pos['entry_price'])
            
            if pos['side'] == 'LONG':
                pnl_pct = (current_price - pos['entry_price']) / pos['entry_price'] * 100
            else:  # SHORT
                pnl_pct = (pos['entry_price'] - current_price) / pos['entry_price'] * 100
            
            position_value = pos['size'] * (1 + pnl_pct / 100)
            total_position_value += position_value
            
            holding_days = (datetime.now() - datetime.fromisoformat(pos['entry_time'])).days
            
            positions_detail.append({
                'trade_id': pos['trade_id'],
                'symbol': pos['symbol'],
                'side': pos['side'],
                'entry_price': pos['entry_price'],
                'current_price': current_price,
                'size': pos['size'],
                'current_pnl_pct': round(pnl_pct, 2),
                'position_value': round(position_value, 2),
                'days_holding': holding_days,
                'stop_loss': pos.get('stop_loss'),
                'take_profit': pos.get('take_profit')
            })
        
        # 計算資金使用率
        total_equity = self.capital + total_position_value
        capital_usage_pct = (total_position_value / total_equity * 100) if total_equity > 0 else 0
        
        # 最近5筆交易
        recent_trades = self.trade_history[-5:] if len(self.trade_history) > 0 else []
        
        return {
            'available_capital': round(self.capital, 2),
            'total_equity': round(total_equity, 2),
            'capital_usage_pct': round(capital_usage_pct, 2),
            'active_positions': len(self.positions),
            'positions_detail': positions_detail,
            'recent_trades': recent_trades,
            'statistics': self.statistics
        }
    
    def can_open_position(self, position_size: float, max_usage_pct: float = 80) -> tuple[bool, str]:
        """
        檢查是否可以開倉
        
        Args:
            position_size: 要開倉的資金量
            max_usage_pct: 最大資金使用率
        
        Returns:
            (can_open, reason)
        """
        if position_size > self.capital:
            return False, f"Insufficient capital: need ${position_size:.2f}, available ${self.capital:.2f}"
        
        # 計算開倉後的資金使用率
        context = self.get_current_context()
        current_usage = context['capital_usage_pct']
        
        # 預估新使用率
        new_total_equity = context['total_equity']
        new_usage = ((context['total_equity'] - self.capital + position_size) / new_total_equity * 100)
        
        if new_usage > max_usage_pct:
            return False, f"Capital usage would exceed limit: {new_usage:.1f}% > {max_usage_pct}%"
        
        # 連續虧搃20筆後應暫停
        if self.statistics['consecutive_losses'] >= 3:
            return False, "Consecutive losses >= 3, trading paused for risk management"
        
        return True, "OK"
    
    def open_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        size: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        ai_confidence: Optional[float] = None
    ) -> str:
        """
        開倉
        
        Args:
            symbol: 交易對 (e.g. 'BTCUSDT')
            side: 'LONG' or 'SHORT'
            entry_price: 進場價
            size: 倉位大小 (USDT)
            stop_loss: 止損價
            take_profit: 止盈價
            ai_confidence: AI信心度 (0-100)
        
        Returns:
            trade_id
        """
        trade_id = str(uuid.uuid4())[:8]
        
        position = {
            'trade_id': trade_id,
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'size': size,
            'entry_time': datetime.now().isoformat(),
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'ai_confidence': ai_confidence
        }
        
        self.positions.append(position)
        self.capital -= size
        self.save_state()
        
        print(f"Opened {side} position: {symbol} @ ${entry_price:.2f}, size=${size:.2f}, ID={trade_id}")
        return trade_id
    
    def close_position(self, trade_id: str, exit_price: float, exit_reason: str = 'MANUAL') -> Dict:
        """
        平倉
        
        Args:
            trade_id: 交易ID
            exit_price: 出場價
            exit_reason: 'TP' / 'SL' / 'MANUAL' / 'AI_SIGNAL'
        
        Returns:
            交易記錄
        """
        position = next((p for p in self.positions if p['trade_id'] == trade_id), None)
        
        if not position:
            raise ValueError(f"Position {trade_id} not found")
        
        # 計算盈虧
        if position['side'] == 'LONG':
            pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
        else:  # SHORT
            pnl_pct = (position['entry_price'] - exit_price) / position['entry_price'] * 100
        
        pnl_amount = position['size'] * (pnl_pct / 100)
        final_value = position['size'] + pnl_amount
        
        # 記錄交易
        trade_record = {
            **position,
            'exit_price': exit_price,
            'exit_time': datetime.now().isoformat(),
            'exit_reason': exit_reason,
            'pnl_pct': round(pnl_pct, 2),
            'pnl_amount': round(pnl_amount, 2),
            'outcome': 'win' if pnl_pct > 0 else 'loss',
            'holding_time_hours': (datetime.now() - datetime.fromisoformat(position['entry_time'])).total_seconds() / 3600
        }
        
        self.trade_history.append(trade_record)
        self.positions.remove(position)
        self.capital += final_value
        
        # 更新統計
        self.statistics['total_trades'] += 1
        self.statistics['total_pnl'] += pnl_amount
        
        if pnl_pct > 0:
            self.statistics['winning_trades'] += 1
            self.statistics['consecutive_wins'] += 1
            self.statistics['consecutive_losses'] = 0
        else:
            self.statistics['losing_trades'] += 1
            self.statistics['consecutive_losses'] += 1
            self.statistics['consecutive_wins'] = 0
        
        # 更新最大回撤
        equity = self.capital + sum(p['size'] for p in self.positions)
        drawdown = (self.initial_capital - equity) / self.initial_capital * 100
        if drawdown > self.statistics['max_drawdown']:
            self.statistics['max_drawdown'] = drawdown
        
        self.save_state()
        
        print(f"Closed {position['side']} position: {position['symbol']} @ ${exit_price:.2f}, PnL={pnl_pct:+.2f}% (${pnl_amount:+.2f})")
        return trade_record
    
    def check_stop_conditions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        檢查所有持倉是否觸發止盈/止損
        
        Args:
            current_prices: {'BTCUSDT': 65000, ...}
        
        Returns:
            需要平倉的交易列表
        """
        to_close = []
        
        for pos in self.positions:
            current_price = current_prices.get(pos['symbol'])
            if not current_price:
                continue
            
            should_close = False
            reason = None
            
            if pos['side'] == 'LONG':
                if pos['stop_loss'] and current_price <= pos['stop_loss']:
                    should_close = True
                    reason = 'SL'
                elif pos['take_profit'] and current_price >= pos['take_profit']:
                    should_close = True
                    reason = 'TP'
            else:  # SHORT
                if pos['stop_loss'] and current_price >= pos['stop_loss']:
                    should_close = True
                    reason = 'SL'
                elif pos['take_profit'] and current_price <= pos['take_profit']:
                    should_close = True
                    reason = 'TP'
            
            if should_close:
                to_close.append({
                    'trade_id': pos['trade_id'],
                    'symbol': pos['symbol'],
                    'exit_price': current_price,
                    'exit_reason': reason
                })
        
        return to_close
    
    def get_performance_summary(self) -> Dict:
        """獲取績效摘要"""
        stats = self.statistics
        
        win_rate = (stats['winning_trades'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0
        
        avg_win = 0
        avg_loss = 0
        if len(self.trade_history) > 0:
            wins = [t['pnl_amount'] for t in self.trade_history if t['outcome'] == 'win']
            losses = [t['pnl_amount'] for t in self.trade_history if t['outcome'] == 'loss']
            avg_win = sum(wins) / len(wins) if wins else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        total_return_pct = (self.capital - self.initial_capital) / self.initial_capital * 100
        
        return {
            'total_trades': stats['total_trades'],
            'win_rate': round(win_rate, 2),
            'total_pnl': round(stats['total_pnl'], 2),
            'total_return_pct': round(total_return_pct, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(stats['max_drawdown'], 2),
            'consecutive_wins': stats['consecutive_wins'],
            'consecutive_losses': stats['consecutive_losses'],
            'current_capital': round(self.capital, 2),
            'initial_capital': self.initial_capital
        }
    
    def reset(self):
        """重置到初始狀態"""
        self.capital = self.initial_capital
        self.positions = []
        self.trade_history = []
        self.statistics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'consecutive_losses': 0,
            'consecutive_wins': 0
        }
        self.save_state()
        print(f"Portfolio reset to initial capital: ${self.initial_capital:.2f}")
