import os
import sys
import json
import argparse
from config_loader import get_config

def run_cloud_groq(audio_path: str, api_key: str, model: str = "whisper-large-v3") -> list:
    """使用 Groq API 执行极速云端语音转写"""
    try:
        from groq import Groq
    except ImportError:
        raise ImportError("请先安装 groq: pip install groq")

    client = Groq(api_key=api_key)
    with open(audio_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f.read()),
            model=model,
            response_format="verbose_json",
        )
    
    # 提取 segments
    results = []
    # Groq verbose_json 返回 segments
    segments = getattr(transcription, "segments", [])
    if isinstance(segments, list):
        for s in segments:
            results.append({
                "start": s.get("start") if isinstance(s, dict) else getattr(s, "start", 0),
                "end": s.get("end") if isinstance(s, dict) else getattr(s, "end", 0),
                "text": (s.get("text") if isinstance(s, dict) else getattr(s, "text", "")).strip()
            })
    else:
        results.append({
            "start": 0,
            "end": 0,
            "text": getattr(transcription, "text", "")
        })
    return results

def run_local_whisper(audio_path: str, model_size: str = "small", device: str = "auto") -> list:
    """使用本地 faster-whisper 执行语音转写"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ImportError("请先安装 faster-whisper: pip install faster-whisper")

    model = WhisperModel(model_size, device=device, compute_type="default")
    segments, info = model.transcribe(audio_path, beam_size=5)
    
    results = []
    for s in segments:
        results.append({
            "start": s.start,
            "end": s.end,
            "text": s.text.strip()
        })
    return results

def main():
    parser = argparse.ArgumentParser(description="ASR 语音转文字调度适配器")
    parser.add_argument("audio_path", help="待转写的音频文件路径")
    parser.add_argument("--output", help="输出 JSON 结果路径", default=None)
    args = parser.parse_args()

    if not os.path.exists(args.audio_path):
        print(json.dumps({"error": f"音频文件不存在: {args.audio_path}"}))
        sys.exit(1)

    cfg = get_config()
    asr_cfg = cfg.get("asr", {})
    mode = asr_cfg.get("mode", "cloud")

    try:
        if mode == "cloud":
            cloud_cfg = asr_cfg.get("cloud", {})
            provider = cloud_cfg.get("provider", "groq")
            if provider == "groq":
                key = cloud_cfg.get("groq_api_key") or os.environ.get("GROQ_API_KEY")
                if not key or "GROQ_API_KEY" in key:
                    raise ValueError("未配置有效 GROQ_API_KEY，请在 config.yaml 或环境变量中配置")
                res = run_cloud_groq(args.audio_path, key, cloud_cfg.get("model", "whisper-large-v3"))
            else:
                raise NotImplementedError(f"未支持的云端 ASR: {provider}")
        else:
            local_cfg = asr_cfg.get("local", {})
            res = run_local_whisper(
                args.audio_path,
                model_size=local_cfg.get("model_size", "small"),
                device=local_cfg.get("device", "auto")
            )

        out_json = json.dumps({"status": "success", "subtitles": res}, ensure_ascii=False, indent=2)
    except Exception as e:
        out_json = json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json)
    else:
        print(out_json)

if __name__ == "__main__":
    main()
