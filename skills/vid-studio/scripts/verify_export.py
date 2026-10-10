#!/usr/bin/env python3
"""Inspect and decode an export; report technical evidence, not aesthetic approval."""

import argparse
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path


def stream_duration(stream):
    """Avoid treating container duration as coverage of every stream."""
    if stream.get("duration") not in (None, "N/A"):
        return float(stream["duration"])
    if stream.get("duration_ts") is not None and stream.get("time_base"):
        return float(stream["duration_ts"]) * float(Fraction(stream["time_base"]))
    if stream.get("codec_type") == "video" and stream.get("nb_frames") not in (None, "N/A"):
        return float(stream["nb_frames"]) / float(Fraction(stream["avg_frame_rate"]))
    return None


def verify(path, width, height, fps, duration, require_audio=False, decode=False, audio_start=0, audio_duration=None):
    path = Path(path).expanduser().resolve()
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("Video must be a nonempty local file")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    metadata = json.loads(probe.stdout)
    videos = [s for s in metadata.get("streams", []) if s.get("codec_type") == "video"]
    audio = [s for s in metadata.get("streams", []) if s.get("codec_type") == "audio"]
    issues = []
    if len(videos) != 1:
        issues.append(f"Expected one video stream, found {len(videos)}")
    stream = videos[0] if videos else {}
    if (stream.get("width"), stream.get("height")) != (width, height):
        issues.append("Frame dimensions differ from approved dimensions")
    try:
        actual_fps = float(Fraction(stream.get("avg_frame_rate", "0/1")))
    except (ValueError, ZeroDivisionError):
        actual_fps = 0
    if not math.isfinite(actual_fps) or abs(actual_fps - fps) > 0.01:
        issues.append("Average frame rate differs from approved frame rate")
    actual_duration = float(metadata.get("format", {}).get("duration", 0))
    tolerance = max(0.1, 2 / fps)
    if not math.isfinite(actual_duration) or abs(actual_duration - duration) > tolerance:
        issues.append("Duration differs from approved duration beyond frame/sample tolerance")
    video_duration = stream_duration(stream)
    video_start = float(stream.get("start_time", 0))
    if video_duration is None or not math.isfinite(video_duration) or abs(video_duration - duration) > tolerance or abs(video_start) > tolerance:
        issues.append("Video stream does not cover the approved picture duration")
    if stream.get("nb_frames") not in (None, "N/A") and abs(int(stream["nb_frames"]) - round(duration * fps)) > 2:
        issues.append("Video frame count differs from expected picture coverage")
    if require_audio and not audio:
        issues.append("Expected audio stream is missing")
    expected_audio_duration = duration if audio_duration is None else audio_duration
    audio_coverage = []
    for track in audio:
        length = stream_duration(track)
        start = float(track.get("start_time", 0))
        audio_coverage.append({"start": start, "duration": length})
    if require_audio and not any(
        a["duration"] is not None and math.isfinite(a["duration"])
        and a["start"] <= audio_start + tolerance
        and a["start"] + a["duration"] >= audio_start + expected_audio_duration - tolerance
        for a in audio_coverage
    ):
        issues.append("Audio stream does not cover the approved audio interval; unknown coverage is not a pass")
    decode_result = "not_run"
    if decode:
        result = subprocess.run(
            ["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-map", "0:v", "-map", "0:a?", "-f", "null", "-"],
            capture_output=True, text=True,
        )
        decode_result = "passed" if result.returncode == 0 else "failed"
        if result.returncode:
            issues.append("Full decode failed: " + result.stderr.strip()[-2000:])
    return {
        "ok": not issues, "path": str(path), "issues": issues,
        "width": stream.get("width"), "height": stream.get("height"),
        "fps": actual_fps, "duration": actual_duration, "video_duration": video_duration,
        "video_codec": stream.get("codec_name"), "pixel_format": stream.get("pix_fmt"),
        "audio_streams": len(audio), "audio_coverage": audio_coverage, "decode": decode_result,
        "visual_review": "pending", "listening_review": "pending" if audio else "not_applicable",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--fps", type=float, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--require-audio", action="store_true")
    parser.add_argument("--audio-start", type=float, default=0, help="Approved required audio interval start")
    parser.add_argument("--audio-duration", type=float, help="Approved required audio interval length; defaults to video duration")
    parser.add_argument("--decode", action="store_true")
    args = parser.parse_args()
    if args.width <= 0 or args.height <= 0 or not math.isfinite(args.fps) or args.fps <= 0 or not math.isfinite(args.duration) or args.duration <= 0:
        parser.error("Dimensions, fps, and duration must be positive finite values")
    if not math.isfinite(args.audio_start) or args.audio_start < 0 or (args.audio_duration is not None and (not math.isfinite(args.audio_duration) or args.audio_duration <= 0)):
        parser.error("Audio interval must have a nonnegative finite start and positive finite duration")
    try:
        result = verify(args.video, args.width, args.height, args.fps, args.duration, args.require_audio, args.decode, args.audio_start, args.audio_duration)
    except (OSError, ValueError, ZeroDivisionError, subprocess.CalledProcessError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        raise SystemExit(1)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
