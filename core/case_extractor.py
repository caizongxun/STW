"""
獲利交易案例提取器
自動從歷史數據中識別並提取成功交易的完整技術指標特徵
"""
import pandas as pd
import numpy as np
import talib
from typing import Dict, List
import json
from pathlib import Path


class CaseExtractor:
    """提取並格式化獲利交易案例的完整技術特徵"""
    
    def __init__(self):
        self.feature_count = 42  # 40+ 技術指標
        
    def extract_from_trades(self, df: pd.DataFrame, trades: List[Dict]) -> List[Dict]:
        """
        從交易記錄中提取詳細案例
        
        Args:
            df: 完整歷史K線數據（必須包含所有K線，不能只有交易時刻）
            trades: 交易記錄 [{
                'entry_time': '2026-02-15 10:00',
                'exit_time': '2026-02-15 18:00',
                'direction': 'LONG',
                'entry_price': 65000,
                'exit_price': 66500,
                'pnl_pct': 2.3
            }]
        
        Returns:
            詳細案例列表
        """
        # 計算所有技術指標
        df = self._calculate_all_indicators(df)
        
        detailed_cases = []
        
        for trade in trades:
            # 只保留獲利 > 1% 的交易
            if trade.get('pnl_pct', 0) < 1.0:
                continue
                
            try:
                case = self._extract_single_case(df, trade)
                if case:
                    detailed_cases.append(case)
            except Exception as e:
                print(f"⚠️ 提取案例失敗: {e}")
                continue
        
        return detailed_cases
    
    def _calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算所有40+技術指標"""
        df = df.copy()
        
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        # === 趨勢指標 (8個) ===
        df['ema9'] = talib.EMA(close, timeperiod=9)
        df['ema21'] = talib.EMA(close, timeperiod=21)
        df['ema50'] = talib.EMA(close, timeperiod=50)
        df['ema200'] = talib.EMA(close, timeperiod=200)
        macd, macd_signal, macd_hist = talib.MACD(close)
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        df['adx'] = talib.ADX(high, low, close, timeperiod=14)
        
        # === 動能指標 (6個) ===
        df['rsi'] = talib.RSI(close, timeperiod=14)
        df['stoch_k'], df['stoch_d'] = talib.STOCH(high, low, close)
        df['cci'] = talib.CCI(high, low, close, timeperiod=14)
        df['mfi'] = talib.MFI(high, low, close, volume, timeperiod=14)
        df['willr'] = talib.WILLR(high, low, close, timeperiod=14)
        df['roc'] = talib.ROC(close, timeperiod=10)
        
        # === 波動指標 (5個) ===
        df['atr'] = talib.ATR(high, low, close, timeperiod=14)
        bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20)
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower
        df['bb_position'] = (close - bb_lower) / (bb_upper - bb_lower + 1e-10)
        
        # === 成交量指標 (4個) ===
        df['volume_ma20'] = talib.SMA(volume, timeperiod=20)
        df['volume_ratio'] = volume / (df['volume_ma20'] + 1e-10)
        df['obv'] = talib.OBV(close, volume)
        df['ad'] = talib.AD(high, low, close, volume)
        
        # === 價格結構 (5個) ===
        df['high_20'] = df['high'].rolling(20).max()
        df['low_20'] = df['low'].rolling(20).min()
        df['dist_from_high'] = (df['high_20'] - close) / close * 100
        df['dist_from_low'] = (close - df['low_20']) / close * 100
        df['pivot'] = (high + low + close) / 3
        
        # === 市場微觀結構 (6個) ===
        df['body'] = abs(df['close'] - df['open'])
        df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
        df['body_pct'] = df['body'] / (df['high'] - df['low'] + 1e-10) * 100
        
        # 連續陽/陰K
        df['is_bullish'] = (df['close'] > df['open']).astype(int)
        df['consecutive_bull'] = df['is_bullish'].rolling(5).sum()
        df['consecutive_bear'] = (1 - df['is_bullish']).rolling(5).sum()
        
        # === 多週期特徵 (4個) ===
        df['price_change_5'] = close / pd.Series(close).shift(5) - 1
        df['price_change_10'] = close / pd.Series(close).shift(10) - 1
        df['volatility_5'] = pd.Series(close).pct_change().rolling(5).std()
        df['volume_trend'] = talib.LINEARREG_SLOPE(volume, timeperiod=10)
        
        # === 支撐/壓力 (4個) ===
        df['resistance_1'] = df['pivot'] + (df['high'] - df['low'])
        df['support_1'] = df['pivot'] - (df['high'] - df['low'])
        df['dist_to_resistance'] = (df['resistance_1'] - close) / close * 100
        df['dist_to_support'] = (close - df['support_1']) / close * 100
        
        return df
    
    def _extract_single_case(self, df: pd.DataFrame, trade: Dict) -> Dict:
        """提取單一交易的完整特徵"""
        entry_time = pd.to_datetime(trade['entry_time'])
        exit_time = pd.to_datetime(trade['exit_time'])
        
        # 確保時間索引
        if 'timestamp' not in df.columns:
            if isinstance(df.index, pd.DatetimeIndex):
                df['timestamp'] = df.index
            else:
                raise ValueError("DataFrame 必須包含 timestamp 欄位或 DatetimeIndex")
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 找到進場K線的索引
        entry_idx = df[df['timestamp'] <= entry_time].index[-1]
        exit_idx = df[df['timestamp'] <= exit_time].index[-1]
        
        # 提取進場前5根K線的指標變化
        lookback = 5
        start_idx = max(0, entry_idx - lookback)
        
        candles = []
        for i in range(start_idx, entry_idx + 1):
            row = df.iloc[i]
            candle = {
                'time': str(row['timestamp']),
                'position': 'entry' if i == entry_idx else f'entry-{entry_idx - i}',
                'ohlcv': [
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row['volume'])
                ],
                'indicators': self._extract_indicators_at_row(row)
            }
            candles.append(candle)
        
        # 持倉期間關鍵K線（每隔N根取樣，避免太多）
        holding_indices = list(range(entry_idx + 1, exit_idx + 1))
        if len(holding_indices) > 10:
            # 取樣策略：保留前2根、最後2根、中間均勻取6根
            sampled = (
                holding_indices[:2] + 
                holding_indices[2:-2][::max(1, len(holding_indices[2:-2])//6)][:6] +
                holding_indices[-2:]
            )
            holding_indices = sorted(set(sampled))
        
        for i in holding_indices:
            row = df.iloc[i]
            candle = {
                'time': str(row['timestamp']),
                'position': 'exit' if i == exit_idx else f'holding+{i - entry_idx}',
                'ohlcv': [
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row['volume'])
                ],
                'indicators': self._extract_indicators_at_row(row)
            }
            candles.append(candle)
        
        # 計算指標變化趨勢（進場前5根）
        entry_candles = [c for c in candles if 'entry' in c['position']]
        indicator_trends = self._calculate_indicator_trends(entry_candles)
        
        case = {
            'trade_id': f"{trade.get('symbol', 'UNKNOWN')}_{trade['direction']}_{entry_time.strftime('%Y%m%d_%H%M')}",
            'symbol': trade.get('symbol', 'UNKNOWN'),
            'direction': trade['direction'],
            'outcome': f"profit_{trade['pnl_pct']:.2f}%",
            'entry_price': float(trade['entry_price']),
            'exit_price': float(trade['exit_price']),
            'entry_time': str(entry_time),
            'exit_time': str(exit_time),
            'holding_bars': int(exit_idx - entry_idx),
            'candles': candles,
            'indicator_trends': indicator_trends,
            'entry_logic': self._generate_entry_logic(df.iloc[entry_idx], trade['direction']),
            'exit_reason': trade.get('exit_reason', 'UNKNOWN')
        }
        
        return case
    
    def _extract_indicators_at_row(self, row: pd.Series) -> Dict:
        """提取單根K線的所有指標數值"""
        indicators = {}
        
        # 只保留技術指標，排除原始OHLCV和時間
        exclude_cols = ['open', 'high', 'low', 'close', 'volume', 'timestamp', 'time', 'symbol']
        
        for col in row.index:
            if col not in exclude_cols and not pd.isna(row[col]):
                indicators[col] = round(float(row[col]), 4)
        
        return indicators
    
    def _calculate_indicator_trends(self, candles: List[Dict]) -> Dict:
        """計算關鍵指標的趨勢（上升/下降/平穩）"""
        if len(candles) < 3:
            return {}
        
        trends = {}
        key_indicators = ['rsi', 'macd_hist', 'volume_ratio', 'bb_position', 'adx']
        
        for indicator in key_indicators:
            values = []
            for candle in candles:
                val = candle['indicators'].get(indicator)
                if val is not None:
                    values.append(val)
            
            if len(values) >= 3:
                # 計算線性趨勢
                x = np.arange(len(values))
                slope = np.polyfit(x, values, 1)[0]
                
                if abs(slope) < 0.01:
                    trend = 'flat'
                elif slope > 0:
                    trend = 'rising'
                else:
                    trend = 'falling'
                
                trends[indicator] = {
                    'trend': trend,
                    'values': [round(v, 2) for v in values],
                    'slope': round(slope, 4)
                }
        
        return trends
    
    def _generate_entry_logic(self, row: pd.Series, direction: str) -> str:
        """自動生成進場邏輯描述"""
        conditions = []
        
        rsi = row.get('rsi', 50)
        volume_ratio = row.get('volume_ratio', 1.0)
        bb_position = row.get('bb_position', 0.5)
        macd_hist = row.get('macd_hist', 0)
        adx = row.get('adx', 0)
        
        if direction == 'LONG':
            if rsi < 35:
                conditions.append(f"RSI超賣({rsi:.1f}<35)")
            if volume_ratio > 1.5:
                conditions.append(f"成交量爆發({volume_ratio:.1f}x)")
            if bb_position < 0.25:
                conditions.append(f"布林下軌反彈(BB={bb_position:.2f})")
            if macd_hist > 0:
                conditions.append("MACD金叉")
            if adx > 25:
                conditions.append(f"趨勢強勁(ADX={adx:.1f})")
        else:  # SHORT
            if rsi > 65:
                conditions.append(f"RSI超買({rsi:.1f}>65)")
            if volume_ratio > 1.5:
                conditions.append(f"成交量爆發({volume_ratio:.1f}x)")
            if bb_position > 0.75:
                conditions.append(f"布林上軌回落(BB={bb_position:.2f})")
            if macd_hist < 0:
                conditions.append("MACD死叉")
            if adx > 25:
                conditions.append(f"趨勢強勁(ADX={adx:.1f})")
        
        if not conditions:
            conditions.append("標準技術形態")
        
        return " + ".join(conditions)
    
    def save_cases(self, cases: List[Dict], filepath: str = "data/detailed_success_cases.json"):
        """保存案例到JSON文件"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # 讀取現有案例
        existing_cases = []
        if Path(filepath).exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                existing_cases = data.get('cases', [])
        
        # 去重（根據trade_id）
        existing_ids = {c['trade_id'] for c in existing_cases}
        new_cases = [c for c in cases if c['trade_id'] not in existing_ids]
        
        all_cases = existing_cases + new_cases
        
        output = {
            'version': '2.0',
            'feature_count': self.feature_count,
            'total_cases': len(all_cases),
            'last_updated': pd.Timestamp.now().isoformat(),
            'cases': all_cases
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已保存 {len(new_cases)} 個新案例 (總計 {len(all_cases)} 個)")
        return len(new_cases)
