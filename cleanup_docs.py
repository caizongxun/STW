#!/usr/bin/env python3
"""
清理多餘的 MD 檔案
保留 README.md，刪除其他所有 .md 檔案
"""
import os
import subprocess

md_files_to_delete = [
    "COMPETITION_GUIDE.md",
    "CURRENT_DATA_STATUS.md",
    "DEEPSEEK_R1_SETUP.md",
    "ENABLE_ARBITRATOR.md",
    "HOW_TO_ENABLE_ARBITRATOR.md",
    "OPENROUTER_FIX_2026_03.md",
    "OPENROUTER_SETUP.md",
    "QUICKSTART.md",
    "QUICKSTART_DUAL_MODEL.md",
    "README_DUAL_MODEL.md",
    "README_FLASK.md",
    "STRATEGY_COMPARISON.md",
    "UPGRADE_SUMMARY.md"
]

print("開始清理 MD 檔案...")
print("="*50)

deleted = []
not_found = []

for filename in md_files_to_delete:
    if os.path.exists(filename):
        try:
            # 使用 git rm 刪除
            result = subprocess.run(
                ['git', 'rm', filename],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                deleted.append(filename)
                print(f"✅ 已刪除: {filename}")
            else:
                print(f"❌ 刪除失敗: {filename}")
                print(f"   錯誤: {result.stderr}")
        except Exception as e:
            print(f"❌ 刪除失敗: {filename}")
            print(f"   異常: {e}")
    else:
        not_found.append(filename)
        print(f"⚠️  檔案不存在: {filename}")

print("\n" + "="*50)
print(f"總計: {len(md_files_to_delete)} 個檔案")
print(f"已刪除: {len(deleted)} 個")
print(f"未找到: {len(not_found)} 個")

if deleted:
    print("\n請執行以下命令提交變更：")
    print('git commit -m "chore: 清理多餘MD檔案"')
    print('git push origin main')
