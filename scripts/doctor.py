import os
import sys
import shutil
from config_loader import get_config

def check_env():
    print("=" * 60)
    print("🏥 agent-video-to-blog 环境配置自检 (Doctor)")
    print("=" * 60)

    all_passed = True

    # 1. 检查 FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print(f"[✓] FFmpeg 安装正常: {ffmpeg_path}")
    else:
        print("[✗] FFmpeg 未找到！请先安装 ffmpeg (如 brew install ffmpeg / apt install ffmpeg)")
        all_passed = False

    # 2. 检查 Python 核心包
    for pkg in ["yaml", "requests"]:
        try:
            __import__(pkg)
            print(f"[✓] 基础依赖 {pkg} OK")
        except ImportError:
            print(f"[✗] 缺少依赖: {pkg} (请执行 pip install -r requirements.txt)")
            all_passed = False

    for pkg, name in [("yt_dlp", "yt-dlp"), ("notion_client", "notion-client")]:
        try:
            __import__(pkg)
            print(f"[✓] 媒体/知识库依赖 {name} OK")
        except ImportError:
            print(f"[!] 依赖未安装: {name} (可通过 pip install {name} 安装)")

    # 3. 检查配置文件
    cfg = get_config()
    if not cfg:
        print("[!] 未检测到 config.yaml，请复制 config.example.yaml 为 config.yaml 并填写配置")
    else:
        print("[✓] 配置文件 config.yaml 读取正常")
        notion_cfg = cfg.get("notion", {})
        token = notion_cfg.get("token") or os.environ.get("NOTION_TOKEN")
        db_id = notion_cfg.get("database_id") or os.environ.get("NOTION_DATABASE_ID")

        if token and not "NOTION_TOKEN" in token:
            print("[✓] Notion Token 已配置")
        else:
            print("[!] Notion Token 未填写或未注入环境变量 NOTION_TOKEN")

        if db_id and not "NOTION_DATABASE_ID" in db_id:
            print(f"[✓] Notion Database ID 已配置: {db_id[:8]}...{db_id[-4:]}")
        else:
            print("[!] Notion Database ID 未填写或未注入环境变量 NOTION_DATABASE_ID")

    print("=" * 60)
    if all_passed:
        print("🎉 核心环境检查完毕！可以正常加载此 Skill。")
    else:
        print("⚠️ 存在缺失的环境组件，请按上述提示修复。")
    print("=" * 60)

if __name__ == "__main__":
    check_env()
