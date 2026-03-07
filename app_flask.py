"""
Flask 主伺服器 - 模塊化版本
支持即時更新、多 Tab 同時操作、無閃爍
新增: 三階段仲裁決策系統 (階段1: 雙模型 -> 階段2: 仲裁者 -> 階段3: 交易執行審核)
修正: 啟動時自動讀取 config.json 並設定環境變數
新增: 模型選擇器功能 (支持熱更新)
新增: 分析詳細功能 (顯示prompt和模型回應)
新增: 多時間框架分析 (15m+1h+4h) + 逆勢操作
新增: 強健 JSON 解析器 (自動修復格式錯誤)
新增: AI 聊天室風格介面 (完整顯示所有 AI 回應)
新增: LINE 風格聊天室 (對話模式)
重構: 模塊化結構，拆分成多個路由模塊
修復: 所有 prepare_market_features 調用都添加 symbol 參數
"""
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
import os

# 初始化 Flask 應用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 嘗試載入功能模塊
try:
    from core.config_manager import ConfigManager
    from core.multi_api_manager import MultiAPIManager
    from core.dual_model_agent import DualModelDecisionAgent
    from core.arbitrator_consensus_agent import ArbitratorConsensusAgent
    from core.multi_timeframe_analyzer import MultiTimeframeAnalyzer
    HAS_CONFIG_MANAGER = True
    HAS_DUAL_MODEL = True
    HAS_ARBITRATOR = True
    HAS_MULTI_TIMEFRAME = True
except ImportError as e:
    HAS_CONFIG_MANAGER = False
    HAS_DUAL_MODEL = False
    HAS_ARBITRATOR = False
    HAS_MULTI_TIMEFRAME = False
    print(f"警告: 部分功能不可用 - {e}")

# 嘗試載入模型選擇器
try:
    from api_routes_model_selector import register_model_selector_routes
    HAS_MODEL_SELECTOR = True
except ImportError as e:
    HAS_MODEL_SELECTOR = False
    print(f"警告: 模型選擇器功能不可用 - {e}")

# 嘗試載入分析詳細
try:
    from api_routes_analysis_detail import register_analysis_detail_routes
    HAS_ANALYSIS_DETAIL = True
except ImportError as e:
    HAS_ANALYSIS_DETAIL = False
    print(f"警告: 分析詳細功能不可用 - {e}")

# 嘗試載入 AI 聊天室
try:
    from api_routes_ai_chat import register_ai_chat_routes
    HAS_AI_CHAT = True
except ImportError as e:
    HAS_AI_CHAT = False
    print(f"警告: AI 聊天室功能不可用 - {e}")

# 導入模塊化路由
from routes.config_routes import register_config_routes
from routes.analysis_routes import register_analysis_routes
from routes.trading_routes import register_trading_routes
from core.config_utils import load_config, load_cases
from core.websocket_handlers import register_websocket_handlers

# 應用狀態
app_state = {
    'ai_agent': None,
    'dual_agent': None,
    'arbitrator_agent': None,
    'mt_analyzer': None,
    'use_dual_model': False,
    'use_arbitrator_consensus': False,
    'dual_model_mode': 'consensus',
    'data_loader': None,
    'auto_update_enabled': False,
    'auto_update_thread': None,
    'ai_prediction_logs': [],
    'latest_signal': None,
    'bybit_trader': None,
    'bybit_trading': False,
    'bybit_thread': None,
    'user_config': {},
    'cases': [],
    'config_manager': None,
    'HAS_DUAL_MODEL': HAS_DUAL_MODEL,
    'HAS_ARBITRATOR': HAS_ARBITRATOR,
    'HAS_MULTI_TIMEFRAME': HAS_MULTI_TIMEFRAME
}

if HAS_CONFIG_MANAGER:
    app_state['config_manager'] = ConfigManager()


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # 啟動時自動載入配置並設定環境變數
    load_config(app_state, app_state['config_manager'], HAS_CONFIG_MANAGER)
    load_cases(app_state)
    
    # 註冊模塊化路由
    register_config_routes(app, app_state, app_state['config_manager'], HAS_CONFIG_MANAGER)
    register_analysis_routes(app, app_state)
    register_trading_routes(app, app_state)
    register_websocket_handlers(socketio, app_state)
    
    # 註冊模型選擇器 API 路由 (傳入 app_state 支持熱更新)
    if HAS_MODEL_SELECTOR:
        register_model_selector_routes(app, app_state)
        print("[OK] 模型選擇器功能已啟用 (支持熱更新)")
    
    # 註冊分析詳細 API 路由
    if HAS_ANALYSIS_DETAIL:
        register_analysis_detail_routes(app, app_state)
        print("[OK] 分析詳細功能已啟用")
    
    # 註冊 AI 聊天室 API 路由
    if HAS_AI_CHAT:
        register_ai_chat_routes(app, app_state)
        print("[OK] AI 聊天室功能已啟用")
    
    print("")
    print("=" * 60)
    print("  Flask Server Starting - STW AI Trading System")
    print("=" * 60)
    print("  Access at: http://localhost:5000")
    print("  Features:")
    print("    - Real-time market data from Binance API")
    print("    - WebSocket live updates")
    print("    - Auto AI prediction logging")
    print("    - Config auto-save & restore")
    print("    - Encrypted API keys storage")
    print("    - Multi-API management")
    print("    - Learning cases library")
    print("    - Module-level loading (no page refresh)")
    print("    - Multi-tab simultaneous operation")
    print("    - Decision history tracking (avoid duplicate)")
    print("    - Historical candles with 40+ technical indicators")
    print("    - Modular architecture (routes separated)")
    
    if HAS_MULTI_TIMEFRAME:
        print("    - Multi-timeframe analysis (15m + 1h + 4h)")
        print("    - Counter-trend operation support")
    
    if HAS_MODEL_SELECTOR:
        print("    - Model selector with hot-reload")
    
    if HAS_ANALYSIS_DETAIL:
        print("    - Analysis detail view (prompt + model responses)")
    
    if HAS_AI_CHAT:
        print("    - AI Chat Room (LINE style, full AI responses display)")
    
    if HAS_ARBITRATOR:
        print("    - Three-stage Arbitrator Consensus (A/B -> Arbitrator -> Executor)")
        print("    - Robust JSON parser (auto-fix format errors)")
        print(f"      Enabled: {app_state['use_arbitrator_consensus']}")
    
    if HAS_DUAL_MODEL:
        print("    - Dual-model decision system")
        print(f"      Mode: {app_state['dual_model_mode']}")
        print(f"      Enabled: {app_state['use_dual_model']}")
    
    print("=" * 60)
    
    if HAS_CONFIG_MANAGER:
        print("  Config Manager: Enabled")
        env_keys = []
        if os.getenv('OPENROUTER_API_KEY'):
            env_keys.append('OPENROUTER_API_KEY')
        if os.getenv('GROQ_API_KEY'):
            env_keys.append('GROQ_API_KEY')
        if os.getenv('GOOGLE_API_KEY'):
            env_keys.append('GOOGLE_API_KEY')
        
        if env_keys:
            print(f"  Environment Keys: {', '.join(env_keys)}")
    else:
        print("  Config Manager: Disabled")
    
    if HAS_ARBITRATOR:
        print("  Arbitrator: Enabled (3-stage)")
    else:
        print("  Arbitrator: Disabled")
    
    if HAS_DUAL_MODEL:
        print("  Dual Model: Enabled")
    else:
        print("  Dual Model: Disabled")
    
    if HAS_MULTI_TIMEFRAME:
        print("  Multi-Timeframe: Enabled")
    else:
        print("  Multi-Timeframe: Disabled")
    
    if HAS_MODEL_SELECTOR:
        print("  Model Selector: Enabled (Hot-Reload)")
    else:
        print("  Model Selector: Disabled")
    
    if HAS_ANALYSIS_DETAIL:
        print("  Analysis Detail: Enabled")
    else:
        print("  Analysis Detail: Disabled")
    
    if HAS_AI_CHAT:
        print("  AI Chat Room: Enabled (LINE Style)")
    else:
        print("  AI Chat Room: Disabled")
    
    print("  JSON Parser: Robust (auto-fix Markdown/quotes/format)")
    print("  Symbol Fix: All prepare_market_features calls include symbol parameter")
    print("=" * 60)
    print("")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
