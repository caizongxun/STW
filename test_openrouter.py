"""
OpenRouter API 測試工具
用於檢查 API Key 是否正確配置
"""
import os
import requests
import json

def test_openrouter_api():
    print("\n" + "="*70)
    print("🔧 OpenRouter API 測試")
    print("="*70)
    
    # 檢查 API Key
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        print("❌ 錯誤: 沒有找到 OPENROUTER_API_KEY 環境變數")
        print("\n請執行：")
        print("  set OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE")
        return
    
    print(f"✅ API Key: {api_key[:20]}...{api_key[-10:]}")
    
    # 測試 1: 簡單模型 (DeepSeek V3)
    print("\n" + "-"*70)
    print("🤖 測試 1: DeepSeek V3")
    print("-"*70)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/caizongxun/STW',
        'X-Title': 'STW Trading Bot'
    }
    
    payload = {
        'model': 'deepseek/deepseek-chat',
        'messages': [
            {'role': 'user', 'content': 'Hello, test message. Reply with OK.'}
        ],
        'max_tokens': 50
    }
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ 成功: {content}")
        else:
            print(f"❌ 失敗: {response.text}")
            
    except Exception as e:
        print(f"❌ 異常: {e}")
    
    # 測試 2: Llama 405B
    print("\n" + "-"*70)
    print("🤖 測試 2: Llama 3.1 405B")
    print("-"*70)
    
    payload['model'] = 'meta-llama/llama-3.1-405b-instruct:free'
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ 成功: {content}")
        else:
            print(f"❌ 失敗: {response.text}")
            
    except Exception as e:
        print(f"❌ 異常: {e}")
    
    # 測試 3: 列出所有免費模型
    print("\n" + "-"*70)
    print("📋 測試 3: 獲取免費模型列表")
    print("-"*70)
    
    try:
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=10
        )
        
        if response.status_code == 200:
            models = response.json()['data']
            free_models = [m for m in models if m.get('pricing', {}).get('prompt', '0') == '0']
            
            print(f"✅ 找到 {len(free_models)} 個免費模型")
            print("\n推薦的免費模型：")
            
            recommended = [
                'deepseek/deepseek-chat',
                'deepseek/deepseek-r1:free',
                'meta-llama/llama-3.3-70b-instruct:free',
                'meta-llama/llama-3.1-405b-instruct:free',
                'google/gemini-2.0-flash-thinking-exp:free'
            ]
            
            for model_id in recommended:
                found = any(m['id'] == model_id for m in free_models)
                status = "✅" if found else "❌"
                print(f"  {status} {model_id}")
        else:
            print(f"❌ 無法獲取模型列表: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 異常: {e}")
    
    print("\n" + "="*70)
    print("測試完成")
    print("="*70 + "\n")

if __name__ == '__main__':
    test_openrouter_api()
