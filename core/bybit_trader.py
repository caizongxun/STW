"""
Bybit Demo Trading 自動交易引擎
使用模擬資金 + 真實市場數據 + 真實滑點
整合倉位感知 AI
"""
import time
from datetime import datetime
from typing import Dict, Optional, List
from pybit.unified_trading import HTTP
import pandas as pd
import json


class BybitDemoTrader:
    """
    Bybit Demo Trading 引擎
    - 使用 Demo Trading API (api-demo.bybit.com)
    - 模擬資金,但使用真實市場價格和滑點
    - 支持止損止盈
    - 整合倉位感知 AI
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        demo_mode: str = 'demo',  # 'demo', 'testnet', or 'mainnet'
        symbol: str = 'BTCUSDT',
        max_leverage: int = 10
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
            max_leverage: 最大槓桿倍數 (1-100)
        """
        self.symbol = symbol
        self.max_leverage = max_leverage
        self.demo_mode = demo_mode
        
        # 根據模式選擇 testnet 參數
        if demo_mode == 'testnet':
            testnet = True
        else:
            testnet = False
        
        # 初始化 Bybit HTTP 客戶端
        self.session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # 狀態追蹤
        self.current_position = None
        self.current_leverage = 1
        self.open_orders = []
        self.trade_history = []
    
    def set_leverage(self, leverage: int):
        """設置槓框倍數"""
        try:
            leverage = max(1, min(leverage, self.max_leverage))
            
            result = self.session.set_leverage(
                category="linear",
                symbol=self.symbol,
                buyLeverage=str(leverage),
                sellLeverage=str(leverage)
            )
            
            if result['retCode'] == 0:
                self.current_leverage = leverage
                print(f"[BYBIT] 槓框設置為 {leverage}x")
                return True
            else:
                print(f"[BYBIT] 設置槓框失敗: {result['retMsg']}")
                return False
                
        except Exception as e:
            print(f"[BYBIT] 設置槓框失敗: {e}")
            return False
    
    def get_balance(self) -> Dict:
        """
        獲取帳戶餘額 (嘗試多種帳戶類型)
        
        Returns:
            {
                'total_equity': float,
                'available_balance': float,
                'unrealized_pnl': float
            }
        """
        print("\n[DEBUG] ========== 開始讀取餘額 ==========")
        
        # 1. 嘗試 UNIFIED 帳戶
        print("[DEBUG] 嘗試讀取 UNIFIED 帳戶...")
        try:
            result = self.session.get_wallet_balance(
                accountType="UNIFIED",
                coin="USDT"
            )
            
            print(f"[DEBUG] UNIFIED API 返回: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result['retCode'] == 0 and result['result']['list']:
                account_info = result['result']['list'][0]
                print(f"[DEBUG] UNIFIED 帳戶資訊: {json.dumps(account_info, indent=2, ensure_ascii=False)}")
                
                usdt_info = next(
                    (coin for coin in account_info['coin'] if coin['coin'] == 'USDT'),
                    None
                )
                
                if usdt_info:
                    equity = float(usdt_info['equity'])
                    print(f"[DEBUG] UNIFIED USDT 餘額: {equity}")
                    
                    if equity > 0:
                        print("[DEBUG] ✅ UNIFIED 帳戶有餘額,使用此帳戶")
                        return {
                            'total_equity': equity,
                            'available_balance': float(usdt_info['availableToWithdraw']),
                            'unrealized_pnl': float(usdt_info['unrealisedPnl'])
                        }
                    else:
                        print("[DEBUG] ⚠️ UNIFIED 帳戶餘額為 0,嘗試 CONTRACT")
        except Exception as e:
            print(f"[DEBUG] ❌ UNIFIED 讀取失敗: {e}")
        
        # 2. 嘗試 CONTRACT 帳戶
        print("\n[DEBUG] 嘗試讀取 CONTRACT 帳戶...")
        try:
            result = self.session.get_wallet_balance(
                accountType="CONTRACT",
                coin="USDT"
            )
            
            print(f"[DEBUG] CONTRACT API 返回: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result['retCode'] == 0 and result['result']['list']:
                account_info = result['result']['list'][0]
                print(f"[DEBUG] CONTRACT 帳戶資訊: {json.dumps(account_info, indent=2, ensure_ascii=False)}")
                
                usdt_info = next(
                    (coin for coin in account_info['coin'] if coin['coin'] == 'USDT'),
                    None
                )
                
                if usdt_info:
                    equity = float(usdt_info['equity'])
                    print(f"[DEBUG] CONTRACT USDT 餘額: {equity}")
                    
                    if equity > 0:
                        print("[DEBUG] ✅ CONTRACT 帳戶有餘額,使用此帳戶")
                        return {
                            'total_equity': equity,
                            'available_balance': float(usdt_info['availableToWithdraw']),
                            'unrealized_pnl': float(usdt_info['unrealisedPnl'])
                        }
                    else:
                        print("[DEBUG] ⚠️ CONTRACT 帳戶餘額也為 0")
        except Exception as e:
            print(f"[DEBUG] ❌ CONTRACT 讀取失敗: {e}")
        
        print("[DEBUG] ❌ 所有帳戶類型都無法讀取餘額")
        print("[DEBUG] ========================================\n")
        
        return {'total_equity': 0, 'available_balance': 0, 'unrealized_pnl': 0}
    
    def get_position(self) -> Optional[Dict]:
        """獲取當前持倉"""
        try:
            result = self.session.get_positions(
                category="linear",
                symbol=self.symbol
            )
            
            if result['retCode'] == 0 and result['result']['list']:
                pos = result['result']['list'][0]
                
                if float(pos['size']) > 0:
                    self.current_position = {
                        'side': pos['side'],
                        'size': float(pos['size']),
                        'entry_price': float(pos['avgPrice']),
                        'current_price': float(pos['markPrice']),
                        'unrealized_pnl': float(pos['unrealisedPnl']),
                        'leverage': int(pos['leverage'])
                    }
                    self.current_leverage = int(pos['leverage'])
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
    
    def get_account_info(self) -> Dict:
        """獲取帳戶資訊 (供AI使用)"""
        balance = self.get_balance()
        balance['max_leverage'] = self.max_leverage
        return balance
    
    def place_market_order(
        self,
        side: str,
        quantity: float,
        leverage: Optional[int] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict:
        """下市價單"""
        try:
            if leverage and leverage != self.current_leverage:
                self.set_leverage(leverage)
            
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
            time.sleep(1)
            
            if stop_loss or take_profit:
                self._set_stop_loss_take_profit(side, stop_loss, take_profit)
            
            self.trade_history.append({
                'time': datetime.now().isoformat(),
                'side': side,
                'quantity': quantity,
                'leverage': self.current_leverage,
                'order_id': order_id,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            })
            
            return {
                'success': True,
                'order_id': order_id,
                'message': f'{side} {quantity} @ Market ({self.current_leverage}x)'
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
                "positionIdx": 0
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
    
    def close_position(self, size: Optional[float] = None) -> Dict:
        """平倉當前持倉"""
        position = self.get_position()
        
        if not position:
            return {'success': False, 'message': '沒有持倉'}
        
        close_size = size if size else position['size']
        close_side = 'Sell' if position['side'] == 'Buy' else 'Buy'
        
        result = self.place_market_order(
            side=close_side,
            quantity=close_size
        )
        
        if result['success']:
            return {
                'success': True,
                'message': f"平倉成功: {position['side']} {close_size} @ Market"
            }
        else:
            return {
                'success': False,
                'message': f"平倉失敗: {result['message']}"
            }
    
    def execute_ai_decision(self, decision: Dict, market_data: Dict) -> Dict:
        """執行 AI 決策"""
        action = decision.get('action', 'HOLD')
        
        if action == 'HOLD':
            return {'action': 'HOLD', 'success': True, 'message': 'AI 建議觀望,不操作'}
        
        elif action == 'CLOSE':
            return self.close_position()
        
        elif action == 'REDUCE_POSITION':
            position = self.get_position()
            if position:
                reduce_size = position['size'] * 0.5
                result = self.close_position(size=reduce_size)
                result['action'] = 'REDUCE_POSITION'
                return result
            else:
                return {'action': 'REDUCE_POSITION', 'success': False, 'message': '無持倉可減'}
        
        elif action == 'ADD_POSITION':
            position = self.get_position()
            if position:
                current_position_value = position['size'] * position['entry_price']
                add_size_usdt = current_position_value * 0.5
                current_price = market_data.get('close', self.get_current_price())
                add_quantity = add_size_usdt / current_price
                
                result = self.place_market_order(
                    side=position['side'],
                    quantity=round(add_quantity, 3),
                    leverage=decision.get('leverage', self.current_leverage),
                    stop_loss=decision.get('stop_loss'),
                    take_profit=decision.get('take_profit')
                )
                result['action'] = 'ADD_POSITION'
                return result
            else:
                return {'action': 'ADD_POSITION', 'success': False, 'message': '無持倉可加'}
        
        elif action == 'OPEN_LONG':
            position = self.get_position()
            if position and position['side'] == 'Sell':
                close_result = self.close_position()
                if not close_result['success']:
                    return close_result
                time.sleep(1)
            
            current_price = market_data.get('close', self.get_current_price())
            position_size_usdt = decision.get('position_size_usdt', 100.0)
            quantity = position_size_usdt / current_price
            
            result = self.place_market_order(
                side='Buy',
                quantity=round(quantity, 3),
                leverage=decision.get('leverage', 1),
                stop_loss=decision.get('stop_loss'),
                take_profit=decision.get('take_profit')
            )
            result['action'] = 'OPEN_LONG'
            return result
        
        elif action == 'OPEN_SHORT':
            position = self.get_position()
            if position and position['side'] == 'Buy':
                close_result = self.close_position()
                if not close_result['success']:
                    return close_result
                time.sleep(1)
            
            current_price = market_data.get('close', self.get_current_price())
            position_size_usdt = decision.get('position_size_usdt', 100.0)
            quantity = position_size_usdt / current_price
            
            result = self.place_market_order(
                side='Sell',
                quantity=round(quantity, 3),
                leverage=decision.get('leverage', 1),
                stop_loss=decision.get('stop_loss'),
                take_profit=decision.get('take_profit')
            )
            result['action'] = 'OPEN_SHORT'
            return result
        
        else:
            return {'action': action, 'success': False, 'message': f'不支援的 action: {action}'}
    
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
            'mode': mode_name,
            'current_leverage': self.current_leverage
        }
