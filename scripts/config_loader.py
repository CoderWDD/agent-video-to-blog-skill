import os
import yaml
from pathlib import Path

def get_config(config_path: str = None) -> dict:
    """加载配置并解析环境变量插值"""
    if config_path is None:
        # 默认从当前目录或上级查找 config.yaml / config.example.yaml
        candidates = [
            Path.cwd() / "config.yaml",
            Path(__file__).resolve().parent.parent / "config.yaml",
            Path(__file__).resolve().parent.parent / "config.example.yaml",
        ]
        for p in candidates:
            if p.exists():
                config_path = str(p)
                break

    if not config_path or not os.path.exists(config_path):
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # 替换 ${VAR_NAME} 环境变量
    for key, val in os.environ.items():
        raw_text = raw_text.replace(f"${{{key}}}", val)

    data = yaml.safe_load(raw_text) or {}
    return data
