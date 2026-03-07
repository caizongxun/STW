"""
API 路由 - AI 聊天室風格分析介面
左邊顯示三個 AI 的完整輸出，右邊顯示我們給 AI 的 prompt
新增: LINE 風格聊天室介面

修復:
- 增強錯誤處理和調試信息
- 確保 raw_content 一定有值
- 更清楚的錯誤提示
"""
from flask import jsonify, render_template
import json


def register_ai_chat_routes(app, app_state):
    """註冊 AI 聊天室 API 路由"""
    
    @app.route('/ai-chat')
    def ai_chat_page():
        """渲染 LINE 風格 AI 聊天室介面"""
        return render_template('ai_chat_line_style.html')
    
    @app.route('/api/ai-chat-data', methods=['GET'])
    def get_ai_chat_data():
        """
        獲取最新一次 AI 分析的完整內容
        返回格式：
        {
            'success': true/false,
            'data': {
                'timestamp': '時間戳',
                'system_prompt': '系統 prompt',
                'user_prompt': '用戶 prompt',
                'model_responses': {
                    'model_a': {...},
                    'model_b': {...},
                    'arbitrator': {...},
                    'executor': {...}
                },
                'final_decision': {...}
            }
        }
        """
        try:
            print("\n" + "="*70)
            print("[AI-CHAT] 收到聊天室數據請求")
            print("="*70)
            
            # 調試: 檢查 app_state 配置
            print(f"[DEBUG] use_arbitrator_consensus: {app_state.get('use_arbitrator_consensus')}")
            print(f"[DEBUG] HAS_ARBITRATOR: {app_state.get('HAS_ARBITRATOR')}")
            
            # 檢查是否有仲裁者
            arbitrator_agent = app_state.get('arbitrator_agent')
            print(f"[DEBUG] arbitrator_agent: {arbitrator_agent is not None}")
            
            if not arbitrator_agent:
                error_msg = "仲裁者未初始化"
                print(f"[ERROR] {error_msg}")
                print("[HINT] 請檢查:")
                print("  1. app.py 中 USE_ARBITRATOR_CONSENSUS = True")
                print("  2. 已執行過「獲取實時訊息」")
                print("  3. arbitrator_agent 已初始化")
                return jsonify({
                    'success': False,
                    'message': f'{error_msg}，請先點擊「獲取實時訊息」',
                    'debug': {
                        'use_arbitrator': app_state.get('use_arbitrator_consensus'),
                        'has_arbitrator_module': app_state.get('HAS_ARBITRATOR')
                    }
                })
            
            # 檢查是否有 get_last_analysis_detail 方法
            if not hasattr(arbitrator_agent, 'get_last_analysis_detail'):
                error_msg = "arbitrator_agent 缺少 get_last_analysis_detail 方法"
                print(f"[ERROR] {error_msg}")
                return jsonify({
                    'success': False,
                    'message': f'{error_msg}，請檢查代碼版本'
                })
            
            # 獲取分析詳細
            analysis_detail = arbitrator_agent.get_last_analysis_detail()
            print(f"[DEBUG] analysis_detail: {analysis_detail is not None}")
            
            if not analysis_detail:
                error_msg = "尚無分析數據"
                print(f"[WARNING] {error_msg}")
                print("[HINT] analysis_detail is None，可能原因:")
                print("  1. 尚未執行過分析")
                print("  2. last_analysis_detail 未正確設置")
                return jsonify({
                    'success': False,
                    'message': f'{error_msg}，請先點擊「獲取實時訊息」'
                })
            
            # 提取模型回應
            model_responses = analysis_detail.get('model_responses', {})
            print(f"[DEBUG] model_responses keys: {list(model_responses.keys())}")
            
            # 組織回應數據
            responses = {}
            
            # Model A
            if 'model_a' in model_responses:
                model_a = model_responses['model_a']
                raw_content = model_a.get('raw_content') or model_a.get('reasoning') or '無回應內容'
                responses['model_a'] = {
                    'model_name': model_a.get('model_name', 'Unknown'),
                    'raw_content': raw_content,
                    'action': model_a.get('action', ''),
                    'confidence': model_a.get('confidence', 0),
                    'reasoning': model_a.get('reasoning', '')
                }
                print(f"[DEBUG] Model A raw_content length: {len(raw_content)}")
            
            # Model B
            if 'model_b' in model_responses:
                model_b = model_responses['model_b']
                raw_content = model_b.get('raw_content') or model_b.get('reasoning') or '無回應內容'
                responses['model_b'] = {
                    'model_name': model_b.get('model_name', 'Unknown'),
                    'raw_content': raw_content,
                    'action': model_b.get('action', ''),
                    'confidence': model_b.get('confidence', 0),
                    'reasoning': model_b.get('reasoning', '')
                }
                print(f"[DEBUG] Model B raw_content length: {len(raw_content)}")
            
            # Arbitrator (如果有使用)
            if 'arbitrator' in model_responses:
                arbitrator = model_responses['arbitrator']
                raw_content = arbitrator.get('raw_content') or arbitrator.get('reasoning') or '無回應內容'
                responses['arbitrator'] = {
                    'model_name': arbitrator.get('model_name', 'Unknown'),
                    'raw_content': raw_content,
                    'action': arbitrator.get('action', ''),
                    'confidence': arbitrator.get('confidence', 0),
                    'reasoning': arbitrator.get('reasoning', '')
                }
                print(f"[DEBUG] Arbitrator raw_content length: {len(raw_content)}")
            
            # Executor (執行審核員)
            if 'executor' in model_responses:
                executor = model_responses['executor']
                # 修復: 確保 executor 一定有 raw_content
                raw_content = (
                    executor.get('raw_content') or 
                    executor.get('reasoning') or 
                    f"執行決策: {executor.get('execution_decision', 'UNKNOWN')}\n" +
                    f"最終動作: {executor.get('final_action', 'UNKNOWN')}\n" +
                    f"信心度: {executor.get('adjusted_confidence', 0)}%"
                )
                responses['executor'] = {
                    'model_name': 'Trading Executor',
                    'raw_content': raw_content,
                    'execution_decision': executor.get('execution_decision', ''),
                    'final_action': executor.get('final_action', ''),
                    'adjusted_confidence': executor.get('adjusted_confidence', 0),
                    'reasoning': executor.get('reasoning', '')
                }
                print(f"[DEBUG] Executor raw_content length: {len(raw_content)}")
                print(f"[DEBUG] Executor has raw_content in original: {'raw_content' in executor}")
            
            # 最終決策
            latest_signal = app_state.get('latest_signal')
            final_decision = latest_signal.get('decision', {}) if latest_signal else {}
            
            print(f"[OK] 成功組織回應數據，包含 {len(responses)} 個模型")
            print("="*70 + "\n")
            
            return jsonify({
                'success': True,
                'data': {
                    'timestamp': analysis_detail.get('timestamp', ''),
                    'system_prompt': analysis_detail.get('system_prompt', ''),
                    'user_prompt': analysis_detail.get('user_prompt', ''),
                    'model_responses': responses,
                    'final_decision': final_decision
                }
            })
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] AI 聊天室數據獲取失敗:")
            print(error_trace)
            return jsonify({
                'success': False,
                'error': str(e),
                'trace': error_trace
            }), 500
    
    @app.route('/api/ai-chat/history', methods=['GET'])
    def get_ai_chat_history():
        """獲取歷史 AI 分析記錄（簡化版）"""
        try:
            logs = app_state.get('ai_prediction_logs', [])
            
            # 只返回最近 20 筆
            recent_logs = logs[-20:] if len(logs) > 20 else logs
            
            return jsonify({
                'success': True,
                'total': len(logs),
                'logs': recent_logs
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    print("[OK] AI 聊天室 API 路由已註冊 (LINE 風格 + 增強調試)")
