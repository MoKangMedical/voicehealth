#!/usr/bin/env python3
"""Generate platform-ready publishing briefs from the VoiceHealth launch queue."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from course_audio_pipeline import repo_root
from generate_marketing_assets import ASSET_ROOT, slug


DEFAULT_SOURCE = Path("data/marketing/publish_queue_9d.json")
DEFAULT_MANIFEST = ASSET_ROOT / "manifest.json"
DEFAULT_OUTPUT_DIR = Path("data/marketing/publish_briefs")
DEFAULT_READY_JSON = Path("data/marketing/publish_queue_ready.json")
DEFAULT_CSV = Path("data/marketing/publish_queue_ready.csv")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads((repo_root() / path).read_text(encoding="utf-8"))


def load_manifest(path: Path) -> dict[str, dict[str, Any]]:
    target = repo_root() / path
    if not target.exists():
        return {}
    data = json.loads(target.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data.get("assets", [])}


def asset_paths(item: dict[str, Any], manifest: dict[str, dict[str, Any]]) -> dict[str, str]:
    existing = manifest.get(item["id"], {})
    if existing:
        return {key: value for key, value in existing.items() if key in {"png", "audio", "video"}}

    base = slug(item["id"])
    if item["channel"] == "小红书":
        return {"png": str(ASSET_ROOT / "xiaohongshu" / f"{base}.png")}
    subdir = "douyin" if item["channel"] == "抖音" else "digital-human"
    return {
        "png": str(ASSET_ROOT / subdir / f"{base}.png"),
        "audio": str(ASSET_ROOT / subdir / f"{base}.mp3"),
        "video": str(ASSET_ROOT / subdir / f"{base}.mp4"),
    }


def publish_time(day: int, channel: str) -> str:
    if channel == "小红书":
        return f"D+{day} 20:30"
    if channel == "抖音":
        return f"D+{day} 12:20"
    return f"D+{day} 18:40"


def channel_slug(channel: str) -> str:
    return {
        "小红书": "xiaohongshu",
        "抖音": "douyin",
        "数字人": "digital-human",
    }.get(channel, slug(channel))


def brief_markdown(item: dict[str, Any], assets: dict[str, str]) -> str:
    tags = " ".join(f"#{tag}" for tag in item.get("tags", []))
    asset_lines = "\n".join(f"- {key}: `{value}`" for key, value in assets.items())
    return f"""# {item['day']:02d} · {item['channel']} · {item['title']}

## 发布设置

- 平台：{item['channel']}
- 形式：{item['format']}
- 建议时间：{publish_time(item['day'], item['channel'])}
- 素材ID：`{item['id']}`

## 标题

{item['title']}

## 正文/口播

{item['copy']}

## 发布正文

{item.get('caption', item['copy'])}

## 标签

{tags}

## 首评

{item.get('firstComment', '内容仅用于健康管理参考，不构成医学诊断或治疗建议。')}

## 转化引导

{item['cta']}

## 素材路径

{asset_lines}

## 发布前合规检查

- 已保留健康管理参考和非诊断声明
- 未使用确诊、治愈、有效率、替代体检等承诺表达
- 数字人或AI合成内容已显著标注AI生成
- 未使用医生、专家或患者见证作为广告推荐
"""


def build_ready_item(item: dict[str, Any], assets: dict[str, str]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "day": item["day"],
        "channel": item["channel"],
        "format": item["format"],
        "title": item["title"],
        "scheduledTime": publish_time(item["day"], item["channel"]),
        "copy": item["copy"],
        "caption": item.get("caption", item["copy"]),
        "tags": item.get("tags", []),
        "firstComment": item.get("firstComment", "内容仅用于健康管理参考，不构成医学诊断或治疗建议。"),
        "cta": item["cta"],
        "assets": assets,
        "status": "ready_for_manual_publish",
    }


def write_csv(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "day",
        "scheduledTime",
        "channel",
        "format",
        "title",
        "caption",
        "tags",
        "firstComment",
        "cta",
        "png",
        "audio",
        "video",
        "status",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item in items:
            assets = item.get("assets", {})
            writer.writerow(
                {
                    "day": item["day"],
                    "scheduledTime": item["scheduledTime"],
                    "channel": item["channel"],
                    "format": item["format"],
                    "title": item["title"],
                    "caption": item["caption"],
                    "tags": " ".join(f"#{tag}" for tag in item.get("tags", [])),
                    "firstComment": item["firstComment"],
                    "cta": item["cta"],
                    "png": assets.get("png", ""),
                    "audio": assets.get("audio", ""),
                    "video": assets.get("video", ""),
                    "status": item["status"],
                }
            )


def generate(source: Path, manifest_path: Path, output_dir: Path, ready_json: Path, csv_path: Path | None) -> dict[str, Any]:
    root = repo_root()
    data = load_json(source)
    manifest = load_manifest(manifest_path)
    out_dir = root / output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    ready_items = []
    title = data.get("campaign", "VoiceHealth 发布简报")
    index_lines = [
        f"# {title}",
        "",
        "所有内容仅用于健康管理参考，不构成医学诊断或治疗建议。发布前仍需人工复核平台规则、账号身份和素材展示。",
        "",
    ]
    for item in data["items"]:
        assets = asset_paths(item, manifest)
        ready_items.append(build_ready_item(item, assets))
        filename = f"{item['day']:02d}-{channel_slug(item['channel'])}-{slug(item['id'])}.md"
        (out_dir / filename).write_text(brief_markdown(item, assets), encoding="utf-8")
        index_lines.append(f"- D+{item['day']} {item['channel']}：[{item['title']}]({filename})")

    (out_dir / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    ready_payload = {
        "updatedAt": data["updatedAt"],
        "source": str(source),
        "manifest": str(manifest_path),
        "items": ready_items,
        "compliance": data.get("compliance", []),
    }
    (root / ready_json).write_text(json.dumps(ready_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if csv_path:
        write_csv(root / csv_path, ready_items)
    return ready_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate manual publishing briefs for social channels.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ready-json", default=str(DEFAULT_READY_JSON))
    parser.add_argument("--csv", default=str(DEFAULT_CSV))
    args = parser.parse_args()

    payload = generate(
        source=Path(args.source),
        manifest_path=Path(args.manifest),
        output_dir=Path(args.output_dir),
        ready_json=Path(args.ready_json),
        csv_path=Path(args.csv) if args.csv else None,
    )
    print(
        json.dumps(
            {"items": len(payload["items"]), "readyJson": args.ready_json, "csv": args.csv},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
