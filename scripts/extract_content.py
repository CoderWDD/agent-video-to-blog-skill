import os
import re
import json
import subprocess
import argparse
import requests
from pathlib import Path
from config_loader import get_config

def get_bilibili_subtitles(url: str, temp_dir: str) -> dict:
    """提取 B 站视频信息及官方字幕，无字幕则准备音频提取"""
    # 提取 BV 号
    bv_match = re.search(r'(BV[a-zA-Z0-9]+)', url)
    bvid = bv_match.group(1) if bv_match else None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com"
    }

    title = "Bilibili Video"
    cover_url = ""
    subtitles = []

    if bvid:
        try:
            view_res = requests.get(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", headers=headers, timeout=10).json()
            if view_res.get("code") == 0:
                data = view_res.get("data", {})
                title = data.get("title", title)
                cover_url = data.get("pic", "")
                cid = data.get("cid")
                aid = data.get("aid")

                # 尝试请求官方字幕
                if cid and aid:
                    sub_url_api = f"https://api.bilibili.com/x/player/v2?aid={aid}&cid={cid}"
                    sub_res = requests.get(sub_url_api, headers=headers, timeout=10).json()
                    sub_list = sub_res.get("data", {}).get("subtitle", {}).get("subtitles", [])
                    if sub_list:
                        target_sub = sub_list[0].get("subtitle_url")
                        if target_sub:
                            if not target_sub.startswith("http"):
                                target_sub = "https:" + target_sub
                            sub_json = requests.get(target_sub, headers=headers, timeout=10).json()
                            for item in sub_json.get("body", []):
                                subtitles.append({
                                    "start": item.get("from"),
                                    "end": item.get("to"),
                                    "text": item.get("content", "").strip()
                                })
        except Exception as e:
            pass

    return {
        "source": "bilibili",
        "title": title,
        "url": url,
        "cover_url": cover_url,
        "has_native_subtitles": len(subtitles) > 0,
        "subtitles": subtitles
    }

def extract_via_ytdlp(url: str, temp_dir: str) -> dict:
    """使用 yt-dlp 抓取 YouTube、抖音、小红书等平台媒体与字幕"""
    os.makedirs(temp_dir, exist_ok=True)
    out_template = os.path.join(temp_dir, "%(id)s.%(ext)s")
    
    # 1. 尝试仅获取元数据和原生字幕 (不用下载完整视频)
    cmd_meta = [
        "yt-dlp",
        "--dump-json",
        "--no-playlist",
        url
    ]
    try:
        res = subprocess.run(cmd_meta, capture_output=True, text=True, check=True)
        meta = json.loads(res.stdout.split("\n")[0])
        title = meta.get("title", "Media Source")
        cover_url = meta.get("thumbnail", "")
        duration = meta.get("duration", 0)

        # 检查是否有自动/人工字幕
        subtitles = []
        # 如果是 YouTube，尝试直接用 yt-dlp 下载字幕
        sub_cmd = [
            "yt-dlp",
            "--write-subs",
            "--write-auto-subs",
            "--sub-lang", "zh-Hans,zh,zh-TW,zh-Hant,en",
            "--sub-format", "json3/vtt/srt",
            "--skip-download",
            "-o", out_template,
            url
        ]
        subprocess.run(sub_cmd, capture_output=True, text=True)
        
        # 查找字幕文件
        sub_files = list(Path(temp_dir).glob(f"{meta.get('id', '*')}*.json3")) + \
                    list(Path(temp_dir).glob(f"{meta.get('id', '*')}*.vtt"))
        
        has_sub = False
        if sub_files:
            has_sub = True
            for sf in sub_files:
                if str(sf).endswith(".json3"):
                    try:
                        with open(sf, "r", encoding="utf-8") as jf:
                            jdata = json.load(jf)
                            for ev in jdata.get("events", []):
                                seg_text = "".join([s.get("utf8", "") for s in ev.get("segs", [])]).strip()
                                if seg_text:
                                    start_sec = ev.get("tStartMs", 0) / 1000.0
                                    dur_sec = ev.get("dDurationMs", 0) / 1000.0
                                    subtitles.append({
                                        "start": start_sec,
                                        "end": start_sec + dur_sec,
                                        "text": seg_text
                                    })
                        if subtitles:
                            break
                    except Exception:
                        pass

        # 2. 如果没有原生字幕，自动下载轻量音频准备 ASR
        audio_file = None
        if not has_sub:
            audio_template = os.path.join(temp_dir, "%(id)s_audio.%(ext)s")
            cmd_audio = [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "5",
                "-o", audio_template,
                url
            ]
            subprocess.run(cmd_audio, capture_output=True, text=True)
            audio_candidates = list(Path(temp_dir).glob(f"{meta.get('id', '*')}*.mp3"))
            if audio_candidates:
                audio_file = str(audio_candidates[0])

        # 3. 准备下载短视频供抽帧 (如果开启了截帧且视频短)
        video_file = None
        cmd_vid = [
            "yt-dlp",
            "-f", "worst[ext=mp4]/bestvideo[height<=720]+bestaudio/best[height<=720]",
            "-o", out_template,
            url
        ]
        # 后台或按需抓取视频文件供截图
        try:
            subprocess.run(cmd_vid, capture_output=True, text=True, timeout=90)
            vid_candidates = list(Path(temp_dir).glob(f"{meta.get('id', '*')}*.mp4")) + \
                             list(Path(temp_dir).glob(f"{meta.get('id', '*')}*.webm")) + \
                             list(Path(temp_dir).glob(f"{meta.get('id', '*')}*.mkv"))
            if vid_candidates:
                video_file = str(vid_candidates[0])
        except Exception:
            pass

        return {
            "source": "ytdlp",
            "title": title,
            "url": url,
            "cover_url": cover_url,
            "duration": duration,
            "has_native_subtitles": has_sub,
            "subtitles": subtitles,
            "audio_file": audio_file,
            "video_file": video_file
        }
    except Exception as e:
        return {"error": str(e), "url": url}

def main():
    parser = argparse.ArgumentParser(description="多平台音视频与字幕通用提取工具")
    parser.add_argument("url", help="视频或网页链接 (B站/YouTube/抖音/小红书/网页)")
    parser.add_argument("--output", help="输出 json 路径", default=None)
    args = parser.parse_args()

    cfg = get_config()
    temp_dir = cfg.get("media", {}).get("temp_dir", "/tmp/agent-video-to-blog")
    os.makedirs(temp_dir, exist_ok=True)

    url = args.url
    if "bilibili.com" in url or "b23.tv" in url:
        info = get_bilibili_subtitles(url, temp_dir)
        # 如果 B 站无原生字幕，回退给 ytdlp 提取音频
        if not info.get("has_native_subtitles"):
            dlp_info = extract_via_ytdlp(url, temp_dir)
            if not dlp_info.get("error"):
                info.update(dlp_info)
    else:
        info = extract_via_ytdlp(url, temp_dir)

    out_json = json.dumps(info, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json)
    else:
        print(out_json)

if __name__ == "__main__":
    main()
