#!/bin/bash

# 修復 index.html 的腳本

echo "✅ 步驟 1: 回滾 index.html 到上一個正常版本..."
git checkout 96642889a6f00e0f21eef0af2b2c1aa8b76c3ed1 -- templates/index.html

echo "✅ 步驟 2: 在 head 中加入 layout_fix.css..."
sed -i "/<link rel=\"stylesheet\" href=.*style.css.*>/a\\    <link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/layout_fix.css') }}>\" templates/index.html

echo "✅ 步驟 3: 提交更改..."
git add templates/index.html
git commit -m "修復: 正確引入 layout_fix.css"

echo ""
echo "====================================="
echo "✅ 修復完成！"
echo "====================================="
echo ""
echo "請執行："
echo "  python app_flask.py"
echo ""
echo "然後清除瀏覽器快取 (Ctrl+Shift+Delete)"
echo ""
