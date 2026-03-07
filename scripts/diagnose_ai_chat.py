#!/usr/bin/env python3
"""
診斷 AI 聊天室無內容問題
檢查 arbitrator_agent 和 last_analysis_detail 狀態

使用方法:
1. 確保 Flask 應用正在運行 (python app_flask.py)
2. 執行: python scripts/diagnose_ai_chat.py
3. 查看診斷結果和建議
"""
import requests
import json
import sys

def diagnose_ai_chat(base_url='http://localhost:5000'):
    print("=" * 70)
    print("AI 聊天室診斷工具")
    print("=" * 70)
    
    all_passed = True
    
    # 測試 1: 檢查 API 響應
    print("\n[測試 1] 檢查 /api/ai-chat-data 響應...")
    try:
        response = requests.get(f'{base_url}/api/ai-chat-data', timeout=5)
        result = response.json()
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Success: {result.get('success')}")
        
        if not result.get('success'):
            all_passed = False
            print(f"   ❌ 失敗原因: {result.get('message', 'Unknown')}")
            
            # 顯示調試信息
            if 'debug' in result:
                debug_info = result['debug']
                print(f"   調試信息:")
                print(f"     - use_arbitrator: {debug_info.get('use_arbitrator')}")
                print(f"     - has_arbitrator_module: {debug_info.get('has_arbitrator_module')}")
            
            print("\n   可能原因:")
            print("   1. arbitrator_agent 未初始化")
            print("   2. 尚未執行 AI 分析")
            print("   3. last_analysis_detail 為 None")
            print("   4. config.json 中 use_arbitrator_consensus: false")
        else:
            print("   ✅ API 響應成功")
            data = result.get('data', {})
            print(f"   Timestamp: {data.get('timestamp')}")
            print(f"   模型回應:")
            responses = data.get('model_responses', {})
            for model_name in ['model_a', 'model_b', 'arbitrator', 'executor']:
                if model_name in responses:
                    resp = responses[model_name]
                    has_content = bool(resp.get('raw_content'))
                    content_len = len(resp.get('raw_content', '')) if has_content else 0
                    status = '✅ 有內容' if has_content else '❌ 無內容'
                    print(f"     - {model_name}: {status} ({content_len} 字元)")
                    
                    if not has_content:
                        all_passed = False
                        print(f"       Reasoning: {resp.get('reasoning', 'N/A')[:50]}...")
    
    except requests.exceptions.ConnectionError:
        all_passed = False
        print("   ❌ 無法連接到 Flask 應用")
        print("   請確保應用正在運行: python app_flask.py")
        return False
    
    except Exception as e:
        all_passed = False
        print(f"   ❌ 錯誤: {e}")
        return False
    
    # 測試 2: 檢查三階段仲裁統計
    print("\n[測試 2] 檢查 arbitrator 統計...")
    try:
        response = requests.get(f'{base_url}/api/arbitrator/stats', timeout=5)
        result = response.json()
        
        if result.get('enabled'):
            print("   ✅ Arbitrator 已啟用")
            stats = result.get('stats', {})
            print(f"   總決策次數: {stats.get('total_decisions', 0)}")
            print(f"   需要仲裁次數: {stats.get('arbitration_count', 0)}")
            print(f"   意見一致次數: {stats.get('agreement_count', 0)}")
            
            if stats.get('total_decisions', 0) == 0:
                all_passed = False
                print("   ⚠️  警告: 總決策次數為 0，請執行一次分析")
        else:
            all_passed = False
            print("   ❌ Arbitrator 未啟用")
            print("   請檢查 config.json 中:")
            print("   'use_arbitrator_consensus': true")
    
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
    
    # 測試 3: 觸發一次分析
    print("\n[測試 3] 觸發一次 AI 分析...")
    try:
        print("   正在調用 /api/analyze，請稍候...")
        response = requests.post(
            f'{base_url}/api/analyze',
            json={'symbol': 'BTCUSDT', 'timeframe': '15m'},
            timeout=60
        )
        result = response.json()
        
        if 'error' in result:
            all_passed = False
            print(f"   ❌ 分析失敗: {result['error']}")
        else:
            print("   ✅ 分析成功")
            decision = result.get('decision', {})
            print(f"   Model Type: {decision.get('model_type')}")
            print(f"   Action: {decision.get('action')}")
            print(f"   Confidence: {decision.get('confidence')}%")
            
            # 再次檢查 AI 聊天室
            print("\n   重新檢查 AI 聊天室...")
            response = requests.get(f'{base_url}/api/ai-chat-data', timeout=5)
            result = response.json()
            
            if result.get('success'):
                print("   ✅ 現在可以獲取內容了！")
                responses = result['data'].get('model_responses', {})
                print(f"   包含 {len(responses)} 個模型回應")
            else:
                all_passed = False
                print(f"   ❌ 仍然無法獲取內容: {result.get('message')}")
    
    except requests.exceptions.Timeout:
        print("   ⏱️  分析超時（AI 分析需要時間，這是正常的）")
        print("   請稍後手動檢查 http://localhost:5000/ai-chat")
    
    except Exception as e:
        all_passed = False
        print(f"   ❌ 錯誤: {e}")
    
    # 測試 4: 檢查 config.json
    print("\n[測試 4] 檢查 config.json 配置...")
    try:
        import json
        import os
        
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                use_arbitrator = config.get('use_arbitrator_consensus', False)
                print(f"   use_arbitrator_consensus: {use_arbitrator}")
                
                if not use_arbitrator:
                    all_passed = False
                    print("   ❌ 仲裁系統未啟用")
                    print("   請在主頁上面選擇「啟用仲裁系統」後保存配置")
                else:
                    print("   ✅ 仲裁系統已啟用")
        else:
            print("   ⚠️  config.json 不存在")
            print("   請在主頁保存一次配置")
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 診斷完成 - 所有測試通過")
    else:
        print("⚠️  診斷完成 - 發現問題")
    print("=" * 70)
    
    print("\n🛠️  建議:")
    if not all_passed:
        print("1. 檢查 Flask console 的調試輸出")
        print("2. 確保 config.json 中 use_arbitrator_consensus: true")
        print("3. 在主頁選擇「啟用仲裁系統」後保存配置")
        print("4. 執行「獲取實時訊息」後再打開 AI 聊天室")
        print("5. 如果 Executor 無內容，執行: python scripts/fix_arbitrator_else.py")
        print("6. 重啟 Flask 應用: python app_flask.py")
    else:
        print("✅ 系統運作正常！")
    
    print("\n🔗 相關連結:")
    print(f"   - AI 聊天室: {base_url}/ai-chat")
    print(f"   - API 測試: {base_url}/api/ai-chat-data")
    print(f"   - 主頁: {base_url}/")
    
    return all_passed

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AI 聊天室診斷工具')
    parser.add_argument(
        '--url',
        default='http://localhost:5000',
        help='Flask 應用 URL (默認: http://localhost:5000)'
    )
    
    args = parser.parse_args()
    
    success = diagnose_ai_chat(args.url)
    sys.exit(0 if success else 1)
