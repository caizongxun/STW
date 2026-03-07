#!/bin/bash

# 在 index.html 中加入側邊欄收納功能

cd ~/STW

echo "✅ 步驟 1: 在 <head> 中加入 sidebar_toggle.css..."
sed -i '/<link rel="stylesheet" href="{{ url_for('\''static'\'' filename='\''css\/floating_chat.css'\'' }}">/a\    <link rel="stylesheet" href="{{ url_for('\''static'\'' filename='\''css\/sidebar_toggle.css'\'' }}>\' templates/index.html

echo "✅ 步驟 2: 在 </body> 前加入 sidebar_toggle.js..."
sed -i '/<script src="{{ url_for('\''static'\'' filename='\''js\/floating_chat.js'\'' }}"><\/script>/a\    <script src="{{ url_for('\''static'\'' filename='\''js\/sidebar_toggle.js'\'' }}"><\/script>\' templates/index.html

echo "✅ 步驟 3: 提交更改..."
git add templates/index.html
git commit -m "新增: 側邊欄收納功能

加入 sidebar_toggle.css 和 sidebar_toggle.js。"

echo ""
echo "====================================="
echo "✅ 完成！"
echo "====================================="
echo ""
echo "請執行："
echo "  python app_flask.py"
echo ""
echo "功能說明："
echo "  - 點擊左上角漢堡按鈕收起/展開側邊欄"
echo "  - 快捷鍵: Ctrl+B"
echo "  - 狀態會自動記憶"
echo ""
