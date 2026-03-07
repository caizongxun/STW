#!/usr/bin/env python3
"""
移除底下 AI 聊天室 Panel

由於底下的 panel 與懸浮球會衝突，移除它並保留懸浮球功能。

使用方法:
python scripts/remove_duplicate_chat_panel.py
"""
import re
import os
import shutil
from datetime import datetime

def remove_chat_panel():
    index_path = 'templates/index.html'
    
    if not os.path.exists(index_path):
        print(f"❌ 找不到檔案: {index_path}")
        return False
    
    # 備份
    backup_path = f"{index_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(index_path, backup_path)
    print(f"✅ 已備份到: {backup_path}")
    
    # 讀取檔案
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_length = len(content)
    
    # 1. 移除 AI 聊天室 Panel HTML
    pattern_panel = r'<!-- AI 聊天室 Panel -->.*?</div>\s*<!-- /AI 聊天室 Panel -->'
    content = re.sub(pattern_panel, '', content, flags=re.DOTALL)
    
    # 如果沒有結束註解，使用替代模式
    if original_length == len(content):
        pattern_panel_alt = r'<!-- AI 聊天室 Panel -->.*?<div class="ai-chat-panel"[^>]*>.*?</div>\s*</div>\s*</div>'
        content = re.sub(pattern_panel_alt, '', content, flags=re.DOTALL)
    
    # 2. 移除 AI 聊天室相關 CSS
    pattern_css = r'/\* AI 聊天室 Panel 樣式 \*/.*?/\* 隐藏/顯示動效 \*/.*?\.ai-chat-panel\.collapsed .*?\{[^}]*\}'
    content = re.sub(pattern_css, '', content, flags=re.DOTALL)
    
    # 3. 移除 ai_chat.js 引用（保留 floating_chat.js）
    content = re.sub(
        r'<script src="\{\{ url_for\(\'static\', filename=\'js/ai_chat\.js\'\) \}\}"></script>\s*',
        '',
        content
    )
    
    final_length = len(content)
    
    if original_length == final_length:
        print("⚠️  未找到需要移除的內容")
        print("請手動檢查 templates/index.html")
        return False
    
    # 寫回檔案
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    removed_bytes = original_length - final_length
    print(f"✅ 成功移除 {removed_bytes} 字節")
    print(f"✅ 已更新: {index_path}")
    print("")
    print("🚀 修復完成！")
    print("")
    print("建議接下來的步驟:")
    print("1. 重啟 Flask 應用: python app_flask.py")
    print("2. 清除瀏覽器緩存 (Ctrl+Shift+R 或 Ctrl+F5)")
    print("3. 點擊「獲取實時訊息」")
    print("4. 打開右下角的懸浮球")
    print("")
    print("📝 如果需要還原，使用:")
    print(f"cp {backup_path} {index_path}")
    
    return True

if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("移除重複 AI 聊天室 Panel")
    print("="*60)
    print("")
    
    confirm = input("確認移除底下的 AI 聊天室 panel？ (y/N): ")
    
    if confirm.lower() != 'y':
        print("取消操作")
        sys.exit(0)
    
    success = remove_chat_panel()
    sys.exit(0 if success else 1)
