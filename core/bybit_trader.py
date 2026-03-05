"""
Bybit Demo Trading 自動交易引擎
使用模擬資金 + 真實市場數據 + 真實滑點
"""
import time
from datetime import datetime
from typing import Dict, Optional, List
from pybit.unified_trading import HTTP
import pandas as pd


class BybitDemoTrader:
    """
    Bybit Demo Trading 引擎
    - 使用 Demo Trading API (api-demo.bybit.com)
    - 模擬資金，但使用真實市場價格和滑點
    - 支援止損止盈
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        demo_mode: str = 'demo',  # 'demo', 'testnet', or 'mainnet'
        symbol: str = 'BTCUSDT',
        leverage: int = 1
    ):
        """
        Args:
            api_key: Bybit API Key
            api_secret: Bybit API Secret
            demo_mode: 
                - 'demo': Demo Trading (真實市場模擬)
                - 'testnet': Testnet (測試網)
                - 'mainnet': Mainnet (真實盤)
            symbol: 交易對 (例如 BTCUSDT)
            leverage: 槓杆倍數 (1-100)
        """
        self.symbol = symbol
        self.leverage = leverage
        self.demo_mode = demo_mode
        
        # 根據模式選擇 endpoint
        if demo_mode == 'demo':
            # Bybit Demo Trading
            base_url = "https://api-demo.bybit.com"
            testnet = False
        elif demo_mode == 'testnet':
            # Bybit Testnet
            testnet = True
            base_url = None
        else:
            # Bybit Mainnet (真實盤)
            testnet = False
            base_url = None
        
        # 初始化 Bybit HTTP 客戶端
        if base_url:
            self.session = HTTP(
                testnet=testnet,
                api_key=api_key,
                api_secret=api_secret,
                endpoint=base_url  # 使用自定義 endpoint
            )
        else:
            self.session = HTTP(
                testnet=testnet,
                api_key=api_key,
                api_secret=api_secret
            )
        
        # 設置槓杆
        self._set_leverage()
        
        # 狀態追蹤
        self.current_position = None
        self.open_orders = []
        self.trade_history = []
    
    def _set_leverage(self):
        """設置槓杆倍數"""
        try:
            result = self.session.set_leverage(
                category="linear",
                symbol=self.symbol,
                buyLeverage=str(self.leverage),
                sellLeverage=str(self.leverage)
            )
            mode_name = {
                'demo': 'Demo Trading',
                'testnet': 'Testnet',
                'mainnet': 'Mainnet'
            }.get(self.demo_mode, 'Unknown')
            
            print(f"[BYBIT-{mode_name.upper()}] 槓杆設置為 {self.leverage}x: {result['retMsg']}")
        except Exception as e:
            print(f"[BYBIT] 設置槓杆失敗: {e}")
    
    def get_balance(self) -> Dict:
        """
        獲取帳戶餘額
        
        Returns:
            {
                'total_equity': float,
                'available_balance': float,
                'unrealized_pnl': float
            }
        """
        try:
            result = self.session.get_wallet_balance(
                accountType="UNIFIED",
                coin="USDT"
            )
            
            if result['retCode'] == 0:
                account_info = result['result']['list'][0]
                usdt_info = next(
                    (coin for coin in account_info['coin'] if coin['coin'] == 'USDT'),
                    None
                )
                
                if usdt_info:
                    return {
                        'total_equity': float(usdt_info['equity']),
                        'available_balance': float(usdt_info['availableToWithdraw']),
                        'unrealized_pnl': float(usdt_info['unrealisedPnl'])
                    }
            
            return {'total_equity': 0, 'available_balance': 0, 'unrealized_pnl': 0}
            
        except Exception as e:
            print(f"[BYBIT] 獲取餘額失敗: {e}")
            return {'total_equity': 0, 'available_balance': 0, 'unrealized_pnl': 0}
    
    def get_position(self) -> Optional[Dict]:
        """
        獲取當前持倉
        
        Returns:
            {
                'side': 'Buy'/'Sell',
                'size': float,
                'entry_price': float,
                'current_price': float,
                'unrealized_pnl': float,
                'leverage': int
            }
        """
        try:
            result = self.session.get_positions(
                category="linear",
                symbol=self.symbol
            )
            
            if result['retCode'] == 0 and result['result']['list']:
                pos = result['result']['list'][0]
                
                # 檢查是否有持倉
                if float(pos['size']) > 0:
                    self.current_position = {
                        'side': pos['side'],
                        'size': float(pos['size']),
                        'entry_price': float(pos['avgPrice']),
                        'current_price': float(pos['markPrice']),
                        'unrealized_pnl': float(pos['unrealisedPnl']),
                        'leverage': int(pos['leverage'])
                    }
                    return self.current_position
            
            self.current_position = None
            return None
            
        except Exception as e:
            print(f"[BYBIT] 獲取持倉失敗: {e}")
            return None
    
    def get_current_price(self) -> float:
        """獲取當前市價"""
        try:
            result = self.session.get_tickers(
                category="linear",
                symbol=self.symbol
            )
            
            if result['retCode'] == 0:
                return float(result['result']['list'][0]['lastPrice'])
            
            return 0.0
            
        except Exception as e:
            print(f"[BYBIT] 獲取價格失敗: {e}")
            return 0.0
    
    def place_market_order(
        self,
        side: str,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict:
        """
        下市價單
        
        Args:
            side: 'Buy' 或 'Sell'
            quantity: 下單數量 (張數)
            stop_loss: 止損價
            take_profit: 止盈價
        
        Returns:
            {
                'success': bool,
                'order_id': str,
                'message': str
            }
        """
        try:
            # 1. 下市價單
            result = self.session.place_order(
                category="linear",
                symbol=self.symbol,
                side=side,
                orderType="Market",
                qty=str(quantity),
                timeInForce="GTC"
            )
            
            if result['retCode'] != 0:
                return {
                    'success': False,
                    'order_id': '',
                    'message': result['retMsg']
                }
            
            order_id = result['result']['orderId']
            
            # 2. 等待成交
            time.sleep(1)
            
            # 3. 設置止損止盈
            if stop_loss or take_profit:
                self._set_stop_loss_take_profit(side, stop_loss, take_profit)
            
            # 4. 記錄交易
            self.trade_history.append({
                'time': datetime.now().isoformat(),
                'side': side,
                'quantity': quantity,
                'order_id': order_id,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            })
            
            return {
                'success': True,
                'order_id': order_id,
                'message': f'{side} {quantity} @ Market'
            }
            
        except Exception as e:
            return {
                'success': False,
                'order_id': '',
                'message': str(e)
            }
    
    def _set_stop_loss_take_profit(
        self,
        position_side: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ):
        """設置止損止盈"""
        try:
            params = {
                "category": "linear",
                "symbol": self.symbol,
                "positionIdx": 0  # One-way mode
            }
            
            if stop_loss:
                params['stopLoss'] = str(stop_loss)
            
            if take_profit:
                params['takeProfit'] = str(take_profit)
            
            result = self.session.set_trading_stop(**params)
            
            if result['retCode'] == 0:
                print(f"[BYBIT] 止損止盈設置成功: SL={stop_loss}, TP={take_profit}")
            else:
                print(f"[BYBIT] 設置失敗: {result['retMsg']}")
                
        except Exception as e:
            print(f"[BYBIT] 設置止損止盈失敗: {e}")
    
    def close_position(self) -> Dict:
        """
        平倉當前持倉
        
        Returns:
            {
                'success': bool,
                'message': str
            }
        """
        position = self.get_position()
        
        if not position:
            return {'success': False, 'message': '沒有持倉'}
        
        # 反向下單平倉
        close_side = 'Sell' if position['side'] == 'Buy' else 'Buy'
        
        result = self.place_market_order(
            side=close_side,
            quantity=position['size']
        )
        
        if result['success']:
            return {
                'success': True,
                'message': f"平倉成功: {position['side']} {position['size']} @ Market"
            }
        else:
            return {
                'success': False,
                'message': f"平倉失敗: {result['message']}"
            }
    
    def execute_ai_signal(
        self,
        signal: Dict,
        position_size_usdt: float = 100.0
    ) -> Dict:
        """
        執行 AI 交易訊號
        
        Args:
            signal: AI 決策
                {
                    'signal': 'LONG'/'SHORT'/'HOLD',
                    'confidence': 70,
                    'entry_price': 65505.24,
                    'stop_loss': 65221.12,
                    'take_profit': 66073.48,
                    'position_size_pct': 30
                }
            position_size_usdt: 每次下單金額 (USDT)
        
        Returns:
            {
                'action': 'OPEN_LONG'/'OPEN_SHORT'/'CLOSE'/'HOLD',
                'success': bool,
                'message': str
            }
        """
        # 1. 獲取當前持倉
        current_position = self.get_position()
        
        # 2. 如果有持倉，檢查是否需要平倉
        if current_position:
            # 方向相反，先平倉
            if (current_position['side'] == 'Buy' and signal['signal'] == 'SHORT') or \
               (current_position['side'] == 'Sell' and signal['signal'] == 'LONG'):
                close_result = self.close_position()
                if not close_result['success']:
                    return {
                        'action': 'CLOSE',
                        'success': False,
                        'message': close_result['message']
                    }
            
            # 已有持倉且方向相同，不再開新倉
            elif (current_position['side'] == 'Buy' and signal['signal'] == 'LONG') or \
                 (current_position['side'] == 'Sell' and signal['signal'] == 'SHORT'):
                return {
                    'action': 'HOLD',
                    'success': True,
                    'message': f"已有 {current_position['side']} 持倉，不重複開倉"
                }
        
        # 3. 沒有持倉，根據 AI 訊號開倉
        if signal['signal'] == 'LONG':
            # 計算下單數量 (張數)
            current_price = self.get_current_price()
            quantity = position_size_usdt / current_price
            
            result = self.place_market_order(
                side='Buy',
                quantity=round(quantity, 3),
                stop_loss=signal.get('stop_loss'),
                take_profit=signal.get('take_profit')
            )
            
            return {
                'action': 'OPEN_LONG',
                'success': result['success'],
                'message': result['message']
            }
        
        elif signal['signal'] == 'SHORT':
            current_price = self.get_current_price()
            quantity = position_size_usdt / current_price
            
            result = self.place_market_order(
                side='Sell',
                quantity=round(quantity, 3),
                stop_loss=signal.get('stop_loss'),
                take_profit=signal.get('take_profit')
            )
            
            return {
                'action': 'OPEN_SHORT',
                'success': result['success'],
                'message': result['message']
            }
        
        else:  # HOLD
            return {
                'action': 'HOLD',
                'success': True,
                'message': 'AI 建議觀望，不操作'
            }
    
    def get_trade_history_df(self) -> pd.DataFrame:
        """獲取交易歷史 DataFrame"""
        if not self.trade_history:
            return pd.DataFrame()
        
        return pd.DataFrame(self.trade_history)
    
    def get_account_summary(self) -> Dict:
        """獲取帳戶摘要"""
        balance = self.get_balance()
        position = self.get_position()
        
        mode_name = {
            'demo': 'Demo Trading',
            'testnet': 'Testnet',
            'mainnet': 'Mainnet (真實盤)'
        }.get(self.demo_mode, 'Unknown')
        
        return {
            'balance': balance,
            'position': position,
            'total_trades': len(self.trade_history),
            'mode': mode_name
        }
