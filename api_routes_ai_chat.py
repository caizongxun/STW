"""
API 路由 - AI 聊天室風格分析介面
左邊顯示三個 AI 的完整輸出，右邊顯示我們給 AI 的 prompt
"""
from flask import jsonify, render_template
import json


def register_ai_chat_routes(app, app_state):
    """註冊 AI 聊天室 API 路由"""
    
    @app.route('/ai-chat')
    def ai_chat_page():
        """渲染 AI 聊天室介面"""
        return render_template('ai_chat.html')
    
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
                    'model_a': {
                        'model_name': '模型名稱',
                        'raw_content': '完整輸出',
                        'action': '決策',
                        'confidence': '信心度',
                        'reasoning': '理由'
                    },
                    'model_b': {...},
                    'arbitrator': {...},
                    'executor': {...}
                },
                'final_decision': {...}
            }
        }
        """
        try:
            # 檢查是否有仲裁者且有分析詳細
            arbitrator_agent = app_state.get('arbitrator_agent')
            
            if not arbitrator_agent:
                return jsonify({
                    'success': False,
                    'message': '尚未執行 AI 分析，請先點擊「分析市場」'
                })
            
            analysis_detail = arbitrator_agent.get_last_analysis_detail()
            
            if not analysis_detail:
                return jsonify({
                    'success': False,
                    'message': '尚未執行 AI 分析，請先點擊「分析市場」'
                })
            
            # 提取模型回應
            model_responses = analysis_detail.get('model_responses', {})
            
            # 組織回應數據
            responses = {}
            
            # Model A
            if 'model_a' in model_responses:
                responses['model_a'] = {
                    'model_name': model_responses['model_a'].get('model_name', 'Unknown'),
                    'raw_content': model_responses['model_a'].get('raw_content', model_responses['model_a'].get('reasoning', '')),
                    'action': model_responses['model_a'].get('action', ''),
                    'confidence': model_responses['model_a'].get('confidence', 0),
                    'reasoning': model_responses['model_a'].get('reasoning', '')
                }
            
            # Model B
            if 'model_b' in model_responses:
                responses['model_b'] = {
                    'model_name': model_responses['model_b'].get('model_name', 'Unknown'),
                    'raw_content': model_responses['model_b'].get('raw_content', model_responses['model_b'].get('reasoning', '')),
                    'action': model_responses['model_b'].get('action', ''),
                    'confidence': model_responses['model_b'].get('confidence', 0),
                    'reasoning': model_responses['model_b'].get('reasoning', '')
                }
            
            # Arbitrator (如果有使用)
            if 'arbitrator' in model_responses:
                responses['arbitrator'] = {
                    'model_name': model_responses['arbitrator'].get('model_name', 'Unknown'),
                    'raw_content': model_responses['arbitrator'].get('raw_content', model_responses['arbitrator'].get('reasoning', '')),
                    'action': model_responses['arbitrator'].get('action', ''),
                    'confidence': model_responses['arbitrator'].get('confidence', 0),
                    'reasoning': model_responses['arbitrator'].get('reasoning', '')
                }
            
            # Executor (執行審核員)
            if 'executor' in model_responses:
                responses['executor'] = {
                    'model_name': 'Trading Executor',
                    'raw_content': model_responses['executor'].get('raw_content', model_responses['executor'].get('reasoning', '')),
                    'execution_decision': model_responses['executor'].get('execution_decision', ''),
                    'final_action': model_responses['executor'].get('final_action', ''),
                    'adjusted_confidence': model_responses['executor'].get('adjusted_confidence', 0),
                    'reasoning': model_responses['executor'].get('reasoning', '')
                }
            
            # 最終決策
            latest_signal = app_state.get('latest_signal')
            final_decision = latest_signal.get('decision', {}) if latest_signal else {}
            
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
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
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
