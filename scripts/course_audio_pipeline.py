#!/usr/bin/env python3
"""Neural TTS + ffmpeg normalization pipeline for VoiceHealth courses."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_CATALOG = Path("data/courses/voicehealth_core_courses.json")
DEFAULT_OUTPUT_DIR = Path("voiceHealth-miniprogram-v2/miniprogram/audio/courses")
DEFAULT_VOICE = "zh-CN-YunyangNeural"
DEFAULT_RATE = "-7%"
DEFAULT_PITCH = "-2Hz"
DEFAULT_BITRATE = "48k"
LOUDNORM_FILTER = "loudnorm=I=-16:TP=-1.5:LRA=9"
SAMPLE_RATE = "24000"
CHANNELS = "1"


@dataclass(frozen=True)
class CourseAudioJob:
    course_id: str
    title: str
    script: str
    output_path: Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return repo_root() / candidate


def load_catalog(path: str | Path = DEFAULT_CATALOG) -> dict[str, Any]:
    catalog_path = resolve_path(path)
    with catalog_path.open("r", encoding="utf-8") as fh:
        catalog = json.load(fh)
    if not isinstance(catalog.get("courses"), list):
        raise ValueError(f"{catalog_path} must contain a courses array")
    return catalog


def build_jobs(
    catalog: dict[str, Any],
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    selected_ids: set[str] | None = None,
) -> list[CourseAudioJob]:
    out_dir = resolve_path(output_dir)
    jobs: list[CourseAudioJob] = []
    for course in catalog["courses"]:
        course_id = str(course["id"])
        if selected_ids and course_id not in selected_ids:
            continue
        script = str(course.get("spokenScript") or "").strip()
        if not script:
            raise ValueError(f"course {course_id} is missing spokenScript")
        jobs.append(
            CourseAudioJob(
                course_id=course_id,
                title=str(course.get("title", course_id)),
                script=script,
                output_path=out_dir / f"{course_id}.mp3",
            )
        )
    return jobs


def validate_script_length(jobs: Iterable[CourseAudioJob], min_chars: int = 150, max_chars: int = 230) -> None:
    short_or_long = [
        f"{job.course_id}:{len(job.script)}"
        for job in jobs
        if len(job.script) < min_chars or len(job.script) > max_chars
    ]
    if short_or_long:
        joined = ", ".join(short_or_long)
        raise ValueError(f"spokenScript length outside {min_chars}-{max_chars} chars: {joined}")


def require_ffmpeg() -> None:
    for tool in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run([tool, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(f"{tool} is required for audio generation and audit") from exc


async def synthesize_edge_tts(
    job: CourseAudioJob,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH,
    bitrate: str = DEFAULT_BITRATE,
    overwrite: bool = False,
) -> None:
    if job.output_path.exists() and not overwrite:
        print(f"skip {job.course_id}: {job.output_path}")
        return

    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("edge-tts is not installed. Run: pip install -r requirements.txt") from exc

    job.output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="voicehealth_tts_") as tmp_dir:
        raw_path = Path(tmp_dir) / f"{job.course_id}.raw.mp3"
        communicate = edge_tts.Communicate(job.script, voice=voice, rate=rate, pitch=pitch)
        await communicate.save(str(raw_path))
        normalize_audio(raw_path, job.output_path, bitrate)
    print(f"done {job.course_id}: {job.title} -> {job.output_path}")


def normalize_audio(raw_path: Path, output_path: Path, bitrate: str = DEFAULT_BITRATE) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(raw_path),
        "-af",
        LOUDNORM_FILTER,
        "-ar",
        SAMPLE_RATE,
        "-ac",
        CHANNELS,
        "-b:a",
        bitrate,
        str(output_path),
    ]
    subprocess.run(command, check=True)


async def generate_jobs(
    jobs: list[CourseAudioJob],
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH,
    bitrate: str = DEFAULT_BITRATE,
    overwrite: bool = False,
) -> None:
    require_ffmpeg()
    validate_script_length(jobs)
    for job in jobs:
        await synthesize_edge_tts(job, voice=voice, rate=rate, pitch=pitch, bitrate=bitrate, overwrite=overwrite)


def parse_selected_ids(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {item.strip() for item in value.split(",") if item.strip()}


def common_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG), help="课程目录 JSON")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="MP3 输出目录")
    parser.add_argument("--ids", help="仅生成指定课程，逗号分隔，例如 vh-01,vh-02")
    parser.add_argument("--voice", default=os.getenv("VOICEHEALTH_TTS_VOICE", DEFAULT_VOICE))
    parser.add_argument("--rate", default=os.getenv("VOICEHEALTH_TTS_RATE", DEFAULT_RATE))
    parser.add_argument("--pitch", default=os.getenv("VOICEHEALTH_TTS_PITCH", DEFAULT_PITCH))
    parser.add_argument("--bitrate", default=os.getenv("VOICEHEALTH_TTS_BITRATE", DEFAULT_BITRATE))
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有 MP3")
    return parser


def run_core_generation(args: argparse.Namespace) -> None:
    catalog = load_catalog(args.catalog)
    jobs = build_jobs(catalog, args.output_dir, parse_selected_ids(args.ids))
    if not jobs:
        raise SystemExit("No courses selected")
    asyncio.run(
        generate_jobs(
            jobs,
            voice=args.voice,
            rate=args.rate,
            pitch=args.pitch,
            bitrate=args.bitrate,
            overwrite=args.overwrite,
        )
    )


def main() -> None:
    parser = common_parser("Generate VoiceHealth course audio with edge_tts and ffmpeg.")
    args = parser.parse_args()
    try:
        run_core_generation(args)
    except Exception as exc:
        print(f"audio generation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
