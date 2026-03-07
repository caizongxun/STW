"""
API 路由 - 分析詳細資訊
用於顯示每次 AI 分析的 prompt 和 3 個模型的完整回應
"""
from flask import jsonify, request


def register_analysis_detail_routes(app, app_state):
    """
    註冊分析詳細路由
    
    Args:
        app: Flask app 實例
        app_state: 應用狀態字典
    """
    
    @app.route('/api/analysis-detail/latest', methods=['GET'])
    def get_latest_analysis_detail():
        """獲取最近一次分析的詳細資訊"""
        try:
            agent = app_state.get('arbitrator_agent')
            
            if not agent:
                return jsonify({
                    'error': '仲裁系統未啟用',
                    'detail': None
                })
            
            detail = agent.get_last_analysis_detail()
            
            if not detail:
                return jsonify({
                    'error': '無分析記錄',
                    'detail': None
                })
            
            # 格式化回傳資料
            formatted_detail = {
                'timestamp': detail.get('timestamp'),
                'prompts': {
                    'system_prompt': detail.get('system_prompt', ''),
                    'user_prompt': detail.get('user_prompt', '')
                },
                'model_responses': detail.get('model_responses', {}),
                'final_decision': detail.get('final_decision', {})
            }
            
            return jsonify({
                'success': True,
                'detail': formatted_detail
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': str(e),
                'detail': None
            }), 500
    
    @app.route('/api/analysis-detail/export', methods=['GET'])
    def export_analysis_detail():
        """匯出分析詳細為 JSON 檔案"""
        try:
            agent = app_state.get('arbitrator_agent')
            
            if not agent:
                return jsonify({'error': '仲裁系統未啟用'}), 400
            
            detail = agent.get_last_analysis_detail()
            
            if not detail:
                return jsonify({'error': '無分析記錄'}), 400
            
            from flask import Response
            import json
            
            json_str = json.dumps(detail, indent=2, ensure_ascii=False)
            
            return Response(
                json_str,
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment;filename=analysis_detail_{detail.get("timestamp", "unknown")}.json'}
            )
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    print("✅ 分析詳細 API 路由已註冊")
