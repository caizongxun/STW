#!/usr/bin/env python3
"""
自動修復 arbitrator_consensus_agent.py 的 else 分支缺少 raw_content 問題

Bug: AI 聊天室無法顯示 Executor 內容
原因: else 分支沒有保存 'raw_content' 欄位
修復: 添加 executor_content 變量和 'raw_content' 欄位
"""
import sys
from pathlib import Path

def fix_arbitrator_file():
    # 文件路徑（相對於專案根目錄）
    file_path = Path("core/arbitrator_consensus_agent.py")
    
    # 需要替換的原始代碼（第 780-798 行）
    old_code = """            # 儲存執行審核員的回應
            if hasattr(self.trading_executor, 'last_raw_response'):
                self.last_analysis_detail['model_responses']['executor'] = {
                    'raw_content': self.trading_executor.last_raw_response,
                    'execution_decision': execution_review['execution_decision'],
                    'final_action': execution_review['final_action'],
                    'adjusted_confidence': execution_review['adjusted_confidence'],
                    'reasoning': execution_review['executor_reasoning']
                }
            else:
                self.last_analysis_detail['model_responses']['executor'] = {
                    'execution_decision': execution_review['execution_decision'],
                    'final_action': execution_review['final_action'],
                    'adjusted_confidence': execution_review['adjusted_confidence'],
                    'reasoning': execution_review['executor_reasoning']
                }"""
    
    # 修復後的代碼
    new_code = """            # 儲存執行審核員的回應
            if hasattr(self.trading_executor, 'last_raw_response') and self.trading_executor.last_raw_response:
                self.last_analysis_detail['model_responses']['executor'] = {
                    'raw_content': self.trading_executor.last_raw_response,
                    'execution_decision': execution_review['execution_decision'],
                    'final_action': execution_review['final_action'],
                    'adjusted_confidence': execution_review['adjusted_confidence'],
                    'reasoning': execution_review['executor_reasoning']
                }
            else:
                # 當沒有 last_raw_response 時，使用 executor_reasoning 作為顯示內容
                executor_content = execution_review.get('executor_reasoning', '執行審核員回應')
                self.last_analysis_detail['model_responses']['executor'] = {
                    'raw_content': executor_content,  # 確保前端可以顯示
                    'execution_decision': execution_review['execution_decision'],
                    'final_action': execution_review['final_action'],
                    'adjusted_confidence': execution_review['adjusted_confidence'],
                    'reasoning': execution_review['executor_reasoning']
                }"""
    
    try:
        # 檢查文件是否存在
        if not file_path.exists():
            print(f"❌ 錯誤: 找不到文件 {file_path}")
            print("請確保在 STW 專案根目錄執行此腳本")
            return False
        
        print(f"📖 讀取文件: {file_path}")
        # 讀取文件內容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否找到需要替換的代碼
        if old_code not in content:
            print(f"❌ 錯誤: 在 {file_path} 中找不到需要替換的代碼")
            print("可能的原因：")
            print("  1. 文件已經被修改過了")
            print("  2. 代碼格式有差異（空格/縮排）")
            print("\n請檢查第 780-798 行的代碼")
            return False
        
        print("✅ 找到需要修復的代碼段")
        print(f"   原始長度: {len(content):,} 字元")
        
        # 執行替換
        new_content = content.replace(old_code, new_code)
        
        # 備份原文件
        backup_path = file_path.with_suffix('.py.bak')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 備份原文件: {backup_path}")
        
        # 寫入修復後的內容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 成功修復 {file_path}")
        print(f"   修復後長度: {len(new_content):,} 字元")
        print(f"   差異: +{len(new_content) - len(content)} 字元")
        
        print("\n🔧 修改內容：")
        print("   1. if 條件增加非空檢查: 'and self.trading_executor.last_raw_response'")
        print("   2. else 分支增加變量: executor_content = execution_review.get(...)")
        print("   3. else 分支添加欄位: 'raw_content': executor_content")
        
        print("\n✅ 修復完成！")
        print("   請重啟應用以使更改生效")
        return True
        
    except PermissionError:
        print(f"❌ 錯誤: 沒有權限修改文件 {file_path}")
        print("   請確保有寫入權限")
        return False
    except Exception as e:
        print(f"❌ 意外錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*70)
    print("自動修復 arbitrator_consensus_agent.py")
    print("修復 AI 聊天室 Executor 無法顯示的問題")
    print("="*70 + "\n")
    
    success = fix_arbitrator_file()
    
    print("\n" + "="*70)
    if success:
        print("🎉 修復成功！")
        sys.exit(0)
    else:
        print("❌ 修復失敗")
        sys.exit(1)
