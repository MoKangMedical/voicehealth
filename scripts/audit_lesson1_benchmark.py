#!/usr/bin/env python3
"""Audit VoiceHealth generated course audio specs with ffprobe."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from statistics import mean


EXPECTED_SAMPLE_RATE = 24000
EXPECTED_CHANNELS = 1
MIN_DURATION = 20
MAX_DURATION = 75
MAX_BITRATE = 70000


def ffprobe(path: Path) -> dict:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(path),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def inspect_audio(path: Path) -> dict:
    info = ffprobe(path)
    audio_stream = next((stream for stream in info.get("streams", []) if stream.get("codec_type") == "audio"), None)
    if not audio_stream:
        return {"file": str(path), "grade": "F", "issues": ["no audio stream"]}

    duration = float(audio_stream.get("duration") or info.get("format", {}).get("duration") or 0)
    sample_rate = int(audio_stream.get("sample_rate") or 0)
    channels = int(audio_stream.get("channels") or 0)
    bit_rate = int(audio_stream.get("bit_rate") or info.get("format", {}).get("bit_rate") or 0)
    issues: list[str] = []

    if sample_rate != EXPECTED_SAMPLE_RATE:
        issues.append(f"sample_rate={sample_rate}")
    if channels != EXPECTED_CHANNELS:
        issues.append(f"channels={channels}")
    if not (MIN_DURATION <= duration <= MAX_DURATION):
        issues.append(f"duration={duration:.3f}s")
    if bit_rate and bit_rate > MAX_BITRATE:
        issues.append(f"bit_rate={bit_rate}")

    return {
        "file": str(path),
        "duration": round(duration, 3),
        "sampleRate": sample_rate,
        "channels": channels,
        "bitRate": bit_rate,
        "grade": "A" if not issues else "B",
        "issues": issues,
    }


def audit(audio_dir: Path, expect_count: int | None) -> dict:
    files = sorted(audio_dir.glob("*.mp3"))
    results = [inspect_audio(path) for path in files]
    issues = [item for item in results if item["grade"] != "A"]
    if expect_count is not None and len(files) != expect_count:
        issues.append({"file": str(audio_dir), "grade": "F", "issues": [f"expected {expect_count}, found {len(files)}"]})

    durations = [item.get("duration", 0) for item in results if item.get("duration")]
    return {
        "audioDir": str(audio_dir),
        "total": len(files),
        "gradeA": sum(1 for item in results if item["grade"] == "A"),
        "gradeIssues": len(issues),
        "durationMean": round(mean(durations), 3) if durations else 0,
        "results": results,
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit generated lesson MP3 specs.")
    parser.add_argument(
        "--audio-dir",
        default="voiceHealth-miniprogram-v2/miniprogram/audio/courses",
        help="课程 MP3 目录",
    )
    parser.add_argument("--expect-count", type=int, default=None)
    parser.add_argument("--output", default="docs/course-audio-audit.json", help="审计 JSON 输出")
    args = parser.parse_args()

    report = audit(Path(args.audio_dir), args.expect_count)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["gradeIssues"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
