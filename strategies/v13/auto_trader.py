"""
V13 自動交易引擎
每 15 分鐘自動更新 AI 訊號 + 整合新聞分析
"""
import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import traceback

from core.data_loader import DataLoader
from core.llm_agent_v2 import EnhancedDeepSeekAgentV2
from core.portfolio_manager import PortfolioManager
from core.news_fetcher import CryptoNewsFetcher


class AutoTrader:
    """
    V13 自動交易引擎
    - 每 15 分鐘更新一次
    - 整合新聞情緒分析
    - AI 自主決策倉位
    """
    
    def __init__(
        self,
        symbol: str = 'BTCUSDT',
        timeframe: str = '15m',
        capital: float = 10000.0,
        ai_confidence_threshold: float = 0.70,
        enable_news: bool = True,
        news_api_token: Optional[str] = None
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.capital = capital
        self.ai_confidence_threshold = ai_confidence_threshold
        self.enable_news = enable_news
        
        # 初始化核心模組
        self.data_loader = DataLoader()
        self.portfolio_manager = PortfolioManager(initial_capital=capital)
        
        # 初始化新聞獲取器
        self.news_fetcher = None
        if enable_news:
            self.news_fetcher = CryptoNewsFetcher(api_token=news_api_token)
        
        # 初始化 AI 引擎
        self.ai_agent = EnhancedDeepSeekAgentV2(
            portfolio_manager=self.portfolio_manager,
            news_fetcher=self.news_fetcher,
            enable_news=enable_news
        )
        
        # 狀態追蹤
        self.last_update = None
        self.update_history = []
        self.running = False
    
    def get_latest_signal(self) -> Dict:
        """
        獲取最新的 AI 交易訊號
        
        Returns:
            {
                'time': str,
                'symbol': str,
                'signal': 'LONG'/'SHORT'/'HOLD',
                'confidence': float,
                'entry_price': float,
                'stop_loss': float,
                'take_profit': float,
                'position_size_pct': float,
                'reasoning': str,
                'news_summary': Optional[str],
                'error': Optional[str]
            }
        """
        try:
            # 1. 載入最新數據
            df = self.data_loader.load_data(self.symbol, self.timeframe)
            
            if df is None or len(df) < 200:
                return {
                    'time': datetime.now().isoformat(),
                    'symbol': self.symbol,
                    'signal': 'HOLD',
                    'confidence': 0,
                    'error': '數據不足，至少需要 200 根 K 線'
                }
            
            # 2. 獲取當前價格
            current_prices = {self.symbol: df.iloc[-1]['close']}
            
            # 3. 調用 AI 分析
            decision = self.ai_agent.analyze_market(
                df=df,
                symbol=self.symbol,
                current_prices=current_prices,
                max_cases=5
            )
            
            # 4. 整合新聞摘要
            news_summary = None
            if self.enable_news and self.news_fetcher:
                news_symbol = self.symbol.replace('USDT', '')
                news_context = self.news_fetcher.get_news_context_for_trading(news_symbol)
                
                if news_context['has_news']:
                    news_summary = f"{news_context['sentiment'].upper()} ({news_context['news_count']} news) - {news_context['recommendation']}"
            
            # 5. 返回結果
            return {
                'time': datetime.now().isoformat(),
                'symbol': self.symbol,
                'signal': decision.get('signal', 'HOLD'),
                'confidence': decision.get('confidence', 0),
                'entry_price': decision.get('entry_price', 0),
                'stop_loss': decision.get('stop_loss', 0),
                'take_profit': decision.get('take_profit', 0),
                'position_size_pct': decision.get('position_size_pct', 0),
                'reasoning': decision.get('reasoning', 'N/A'),
                'news_summary': news_summary,
                'matched_cases': decision.get('matched_cases', []),
                'market_suitable': decision.get('market_suitable', True)
            }
            
        except Exception as e:
            return {
                'time': datetime.now().isoformat(),
                'symbol': self.symbol,
                'signal': 'HOLD',
                'confidence': 0,
                'error': f'AI 分析失敗: {str(e)}',
                'traceback': traceback.format_exc()
            }
    
    def should_update(self, interval_minutes: int = 15) -> bool:
        """
        檢查是否需要更新
        
        Args:
            interval_minutes: 更新間隔（分鐘）
        
        Returns:
            bool
        """
        if self.last_update is None:
            return True
        
        elapsed = (datetime.now() - self.last_update).total_seconds() / 60
        return elapsed >= interval_minutes
    
    def run_auto_update(self, interval_minutes: int = 15, max_iterations: Optional[int] = None):
        """
        自動更新循環
        
        Args:
            interval_minutes: 更新間隔
            max_iterations: 最大迭代次數（None = 無限）
        """
        self.running = True
        iteration = 0
        
        print(f"🚀 自動交易引擎啟動")
        print(f"   幣種: {self.symbol}")
        print(f"   時間框架: {self.timeframe}")
        print(f"   更新間隔: {interval_minutes} 分鐘")
        print(f"   新聞整合: {'\u2705 啟用' if self.enable_news else '\u274c 關閉'}")
        print("\n" + "="*60 + "\n")
        
        while self.running:
            if max_iterations and iteration >= max_iterations:
                print(f"✅ 達到最大迭代次數 ({max_iterations})，停止")
                break
            
            if self.should_update(interval_minutes):
                iteration += 1
                print(f"🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 第 {iteration} 次更新")
                
                # 獲取訊號
                signal = self.get_latest_signal()
                
                # 記錄歷史
                self.update_history.append(signal)
                self.last_update = datetime.now()
                
                # 顯示結果
                self._display_signal(signal)
                
                # 如果有錯誤，顯示但繼續執行
                if 'error' in signal:
                    print(f"   ⚠️ 錯誤: {signal['error']}\n")
                
                print("\n" + "-"*60 + "\n")
            
            # 等待 1 分鐘後再檢查
            time.sleep(60)
        
        print("✅ 自動交易引擎已停止")
    
    def _display_signal(self, signal: Dict):
        """顯示訊號詳細資訊"""
        print(f"   📊 訊號: {signal['signal']}")
        print(f"   🎯 信心度: {signal['confidence']}%")
        print(f"   💰 進場價: ${signal.get('entry_price', 0):,.2f}")
        print(f"   🛡️ 止損: ${signal.get('stop_loss', 0):,.2f}")
        print(f"   🎯 止盈: ${signal.get('take_profit', 0):,.2f}")
        print(f"   📈 倉位: {signal.get('position_size_pct', 0):.1f}%")
        
        if signal.get('news_summary'):
            print(f"   📰 新聞: {signal['news_summary']}")
        
        if signal.get('matched_cases'):
            print(f"   📚 匹配案例: {len(signal['matched_cases'])} 個")
    
    def stop(self):
        """停止自動更新"""
        self.running = False
    
    def get_history_summary(self) -> pd.DataFrame:
        """
        獲取歷史訊號摘要
        
        Returns:
            DataFrame
        """
        if not self.update_history:
            return pd.DataFrame()
        
        return pd.DataFrame([{
            '時間': h['time'],
            '訊號': h['signal'],
            '信心度': h['confidence'],
            '進場價': h.get('entry_price', 0),
            '倉位%': h.get('position_size_pct', 0),
            '新聞': h.get('news_summary', 'N/A')[:30] + '...' if h.get('news_summary') else 'N/A'
        } for h in self.update_history])


def render_auto_trader_ui():
    """
Streamlit UI 渲染函數
    """
    st.subheader("⏱️ 自動交易引擎")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        symbol = st.selectbox(
            "💰 交易對",
            ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
        )
        
        interval = st.selectbox(
            "⏰ 更新間隔",
            [('15 分鐘', 15), ('30 分鐘', 30), ('1 小時', 60)],
            format_func=lambda x: x[0]
        )[1]
        
        enable_news = st.checkbox(
            "📰 啟用新聞分析",
            value=True,
            help="整合 CryptoPanic API 的新聞情緒分析"
        )
    
    with col2:
        if st.button("🚀 啟動自動更新", type="primary"):
            st.session_state['auto_trader'] = AutoTrader(
                symbol=symbol,
                enable_news=enable_news
            )
            st.session_state['auto_running'] = True
        
        if st.button("⏸️ 停止更新", type="secondary"):
            if 'auto_trader' in st.session_state:
                st.session_state['auto_trader'].stop()
                st.session_state['auto_running'] = False
    
    st.divider()
    
    # 實時顯示
    if 'auto_trader' in st.session_state and st.session_state.get('auto_running'):
        trader = st.session_state['auto_trader']
        
        # 自動刷新區域
        placeholder = st.empty()
        
        while st.session_state.get('auto_running'):
            if trader.should_update(interval):
                signal = trader.get_latest_signal()
                trader.update_history.append(signal)
                trader.last_update = datetime.now()
                
                with placeholder.container():
                    st.success(f"✅ 最新更新: {datetime.now().strftime('%H:%M:%S')}")
                    
                    # 顯示訊號
                    if signal.get('error'):
                        st.error(f"⚠️ {signal['error']}")
                    else:
                        col_s1, col_s2, col_s3 = st.columns(3)
                        col_s1.metric("訊號", signal['signal'])
                        col_s2.metric("信心度", f"{signal['confidence']}%")
                        col_s3.metric("倉位", f"{signal.get('position_size_pct', 0):.1f}%")
                        
                        if signal.get('news_summary'):
                            st.info(f"📰 {signal['news_summary']}")
                    
                    # 歷史訊號
                    st.markdown("### 📊 歷史記錄")
                    history_df = trader.get_history_summary()
                    if not history_df.empty:
                        st.dataframe(history_df.tail(10), use_container_width=True)
            
            time.sleep(10)  # 每 10 秒檢查一次
    
    elif 'auto_trader' in st.session_state:
        st.info("⏸️ 自動更新已停止")
        
        # 顯示歷史
        trader = st.session_state['auto_trader']
        history_df = trader.get_history_summary()
        if not history_df.empty:
            st.markdown("### 📊 歷史記錄")
            st.dataframe(history_df, use_container_width=True)
