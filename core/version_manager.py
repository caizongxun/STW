# 策略版本管理
import importlib
import os

class VersionManager:
    @staticmethod
    def load_versions():
        # 加载所有策略版本
        versions = {}
        strategies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "strategies")
        
        for version_dir in os.listdir(strategies_dir):
            if version_dir.startswith("v") and os.path.isdir(os.path.join(strategies_dir, version_dir)):
                try:
                    version_module = importlib.import_module(f"strategies.{version_dir}")
                    versions[version_dir] = version_module
                except ImportError as e:
                    print(f"加载版本 {version_dir} 失败: {e}")
        
        return versions