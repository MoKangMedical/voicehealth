#!/usr/bin/env python3
"""Generate every VoiceHealth course audio catalog currently present in data/courses."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from audit_lesson1_benchmark import audit
from course_audio_pipeline import (
    DEFAULT_BITRATE,
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_VOICE,
    build_jobs,
    generate_jobs,
    load_catalog,
    repo_root,
)


CATALOG_DIR = Path("data/courses")
MINIPROGRAM_AUDIO_DIR = Path("voiceHealth-miniprogram-v2/miniprogram/audio")


def infer_output_dir(catalog_path: Path) -> Path:
    name = catalog_path.stem.lower()
    if "book" in name or "books" in name:
        return MINIPROGRAM_AUDIO_DIR / "books"
    return MINIPROGRAM_AUDIO_DIR / "courses"


def discover_catalogs(catalog_dir: Path) -> list[Path]:
    root = repo_root()
    resolved = catalog_dir if catalog_dir.is_absolute() else root / catalog_dir
    catalogs = sorted(path for path in resolved.glob("*.json") if path.is_file())
    valid: list[Path] = []
    for path in catalogs:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data.get("courses"), list):
            valid.append(path)
    return valid


async def generate_all(args: argparse.Namespace) -> dict:
    catalogs = discover_catalogs(Path(args.catalog_dir))
    if not catalogs:
        raise SystemExit(f"No course catalogs found in {args.catalog_dir}")

    summary = {
        "catalogs": [],
        "totalCourses": 0,
        "totalAudio": 0,
        "gradeA": 0,
        "gradeIssues": 0,
    }

    for catalog_path in catalogs:
        catalog = load_catalog(catalog_path)
        output_dir = infer_output_dir(catalog_path)
        jobs = build_jobs(catalog, output_dir)
        await generate_jobs(
            jobs,
            voice=args.voice,
            rate=args.rate,
            pitch=args.pitch,
            bitrate=args.bitrate,
            overwrite=args.overwrite,
        )
        report = audit(repo_root() / output_dir, expect_count=len(jobs))
        summary["catalogs"].append(
            {
                "catalog": str(catalog_path.relative_to(repo_root())),
                "outputDir": str(output_dir),
                "courses": len(jobs),
                "audio": report["total"],
                "gradeA": report["gradeA"],
                "gradeIssues": report["gradeIssues"],
                "durationMean": report["durationMean"],
            }
        )
        summary["totalCourses"] += len(jobs)
        summary["totalAudio"] += report["total"]
        summary["gradeA"] += report["gradeA"]
        summary["gradeIssues"] += report["gradeIssues"]

    output_path = repo_root() / args.audit_output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and audit all available VoiceHealth course audio.")
    parser.add_argument("--catalog-dir", default=str(CATALOG_DIR), help="课程 JSON 目录")
    parser.add_argument("--audit-output", default="docs/all-course-audio-audit.json", help="汇总审计输出")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--rate", default=DEFAULT_RATE)
    parser.add_argument("--pitch", default=DEFAULT_PITCH)
    parser.add_argument("--bitrate", default=DEFAULT_BITRATE)
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有音频")
    args = parser.parse_args()
    summary = asyncio.run(generate_all(args))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["gradeIssues"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
