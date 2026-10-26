import os
import sys
import subprocess
import argparse
import json
from pathlib import Path

def capture_frame(video_path: str, timestamp: str, output_path: str = None) -> str:
    """使用 ffmpeg 按指定时间戳 (秒数或 00:04:12) 截取一帧无损图片"""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    if not output_path:
        stem = Path(video_path).stem
        sanitized_ts = str(timestamp).replace(":", "-").replace(".", "_")
        output_path = f"/tmp/{stem}_{sanitized_ts}.jpg"

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(timestamp),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return output_path

def main():
    parser = argparse.ArgumentParser(description="FFmpeg 视频精准截帧工具")
    parser.add_argument("--video", required=True, help="视频文件路径")
    parser.add_argument("--time", required=True, help="时间戳 (秒数如 145 或格式 00:02:25)")
    parser.add_argument("--output", help="图片保存路径", default=None)
    args = parser.parse_args()

    try:
        saved_img = capture_frame(args.video, args.time, args.output)
        print(json.dumps({"status": "success", "image_path": saved_img}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
