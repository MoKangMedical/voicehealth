#!/usr/bin/env python3
"""Generate publish-ready marketing covers and videos for VoiceHealth."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from course_audio_pipeline import DEFAULT_PITCH, DEFAULT_RATE, DEFAULT_VOICE, LOUDNORM_FILTER, repo_root


ASSET_ROOT = Path("assets/marketing")
DEFAULT_SOURCE = Path("data/marketing/growth_assets.json")
XHS_SIZE = (1242, 1660)
VIDEO_SIZE = (1080, 1920)
VIDEO_BITRATE = "1800k"
AUDIO_BITRATE = "64k"
AI_LABEL = "AI数字人生成 · 内容仅供健康管理参考"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def require_tools() -> None:
    for tool in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run([tool, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(f"{tool} is required to generate marketing assets") from exc


def load_assets(path: Path = DEFAULT_SOURCE) -> dict[str, Any]:
    target = repo_root() / path
    return json.loads(target.read_text(encoding="utf-8"))


def slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()
    return value or "asset"


def wrap_text(text: str, width: int) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    no_line_start = "，。！？；：、,.!?;:)"
    lines: list[str] = []
    current = ""
    visual = 0
    for char in text:
        char_width = 1 if ord(char) < 128 else 2
        if char in no_line_start and current:
            current += char
            visual += char_width
            continue
        if visual + char_width > width and current:
            lines.append(current)
            current = char
            visual = char_width
        else:
            current += char
            visual += char_width
    if current:
        lines.append(current)
    return lines


FONT_PATHS = [
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
]


def font(size: int):
    from PIL import ImageFont

    for path in FONT_PATHS:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default(size=size)


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def draw_lines(draw, lines: list[str], x: int, y: int, font_obj, fill: tuple[int, int, int], line_height: int) -> int:
    current = y
    for line in lines:
        draw.text((x, current), line, font=font_obj, fill=fill)
        current += line_height
    return current


def draw_marketing_png(item: dict[str, str], png_path: Path, size: tuple[int, int]) -> None:
    from PIL import Image, ImageDraw, ImageFilter

    width, height = size
    is_avatar = item["channel"] == "数字人"
    channel_color = {
        "小红书": "#f472b6",
        "抖音": "#67e8f9",
        "数字人": "#86efac",
    }.get(item["channel"], "#93c5fd")
    accent = hex_rgb(channel_color)

    image = Image.new("RGB", size, "#0f172a")
    pixels = image.load()
    for y in range(height):
        ratio = y / max(1, height - 1)
        r = int(15 * (1 - ratio) + 8 * ratio)
        g = int(23 * (1 - ratio) + 17 * ratio)
        b = int(42 * (1 - ratio) + 31 * ratio)
        for x in range(width):
            pixels[x, y] = (r, g, b)

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    o = ImageDraw.Draw(overlay)
    o.ellipse((width - 420, 0, width + 210, 610), fill=(*accent, 34))
    o.ellipse((-220, height - 560, 360, height + 120), fill=(134, 239, 172, 18))
    o.rounded_rectangle((76, 82, width - 76, height - 82), radius=48, fill=(2, 6, 23, 120), outline=(255, 255, 255, 28), width=2)
    overlay = overlay.filter(ImageFilter.GaussianBlur(0.2))
    image = Image.alpha_composite(image.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(image)

    label_font = font(34 if width > 1100 else 30)
    title_font = font(74 if width > 1100 else 64)
    body_font = font(38 if width > 1100 else 34)
    cta_font = font(38 if width > 1100 else 34)
    footer_font = font(28 if width > 1100 else 24)

    draw.text((112, 128), f"VoiceHealth · {item['channel']}", font=label_font, fill=accent)

    title_y = 260
    body_y = 540
    if is_avatar:
        cx, cy = width // 2, 550
        draw.ellipse((cx - 190, cy - 190, cx + 190, cy + 190), fill=(96, 165, 250, 220))
        draw.ellipse((cx - 72, cy - 120, cx + 72, cy + 24), fill=(219, 234, 254, 255))
        draw.pieslice((cx - 190, cy - 15, cx + 190, cy + 365), start=180, end=360, fill=(191, 219, 254, 255))
        draw.line((cx - 86, cy - 86, cx + 86, cy - 86), fill=(30, 41, 59, 255), width=16)
        draw.ellipse((cx - 45, cy - 90, cx - 25, cy - 70), fill=(15, 23, 42, 255))
        draw.ellipse((cx + 25, cy - 90, cx + 45, cy - 70), fill=(15, 23, 42, 255))
        draw.arc((cx - 35, cy - 40, cx + 35, cy + 20), start=20, end=160, fill=(15, 23, 42, 255), width=8)
        draw.rounded_rectangle((cx - 220, cy + 260, cx + 220, cy + 330), radius=20, fill=(15, 23, 42, 180), outline=(*accent, 150), width=2)
        draw.text((cx - 168, cy + 278), "AI DIGITAL HEALTH ASSISTANT", font=font(22), fill=(203, 213, 225, 255))
        title_y = 960
        body_y = 1120

    title_lines = wrap_text(item["title"], 18)[:3]
    draw_lines(draw, title_lines, 112, title_y, title_font, (255, 255, 255), int(title_font.size * 1.28))
    body_width = 27 if width < 1200 else 30
    max_body_lines = 10 if is_avatar else 8
    display_copy = item.get("coverCopy", item["copy"])
    body_lines = wrap_text(display_copy, body_width)[:max_body_lines]
    draw_lines(draw, body_lines, 112, body_y, body_font, (203, 213, 225), int(body_font.size * 1.34))

    cta = item.get("cta", "开始体验")
    cta_top = height - 300
    draw.rounded_rectangle((112, cta_top, width - 112, cta_top + 112), radius=26, fill=accent)
    draw.text((150, cta_top + 34), cta, font=cta_font, fill=(6, 17, 31))
    footer = AI_LABEL if is_avatar else "健康管理参考，不构成医学诊断或治疗建议"
    draw.text((112, height - 120), footer, font=footer_font, fill=(148, 163, 184))
    png_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(png_path, quality=95)


def write_png(item: dict[str, str], target_dir: Path, size: tuple[int, int], variant: str) -> dict[str, str]:
    target_dir.mkdir(parents=True, exist_ok=True)
    base = slug(item["id"])
    png_path = target_dir / f"{base}.png"
    draw_marketing_png(item, png_path, size)
    return {"png": str(png_path.relative_to(repo_root()))}


async def synthesize(text: str, output_path: Path) -> None:
    import edge_tts

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="voicehealth_marketing_") as tmp_dir:
        raw = Path(tmp_dir) / "raw.mp3"
        communicate = edge_tts.Communicate(text, voice=DEFAULT_VOICE, rate=DEFAULT_RATE, pitch=DEFAULT_PITCH)
        await communicate.save(str(raw))
        run([
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(raw),
            "-af",
            LOUDNORM_FILTER,
            "-ar",
            "24000",
            "-ac",
            "1",
            "-b:a",
            AUDIO_BITRATE,
            str(output_path),
        ])


def make_video(image_path: Path, audio_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-i",
        str(audio_path),
        "-c:v",
        "libx264",
        "-tune",
        "stillimage",
        "-b:v",
        VIDEO_BITRATE,
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output_path),
    ])


def probe_summary(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(completed.stdout)
    video = next((stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in data.get("streams", []) if stream.get("codec_type") == "audio"), {})
    fmt = data.get("format", {})
    return {
        "video": {
            "codec": video.get("codec_name"),
            "width": video.get("width"),
            "height": video.get("height"),
            "pixFmt": video.get("pix_fmt"),
            "frames": video.get("nb_frames"),
        },
        "audio": {
            "codec": audio.get("codec_name"),
            "sampleRate": audio.get("sample_rate"),
            "channels": audio.get("channels"),
            "layout": audio.get("channel_layout"),
        },
        "format": {
            "duration": fmt.get("duration"),
            "size": fmt.get("size"),
            "bitRate": fmt.get("bit_rate"),
        },
    }


def source_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    items = data.get("readyToPublish") or data.get("items")
    if not isinstance(items, list):
        raise ValueError("Marketing source must include readyToPublish or items list")
    return items


def compliance_items(data: dict[str, Any]) -> list[str]:
    return data.get("complianceChecklist") or data.get("compliance") or []


async def generate_assets(source: Path = DEFAULT_SOURCE, overwrite: bool = False) -> dict[str, Any]:
    require_tools()
    root = repo_root()
    data = load_assets(source)
    generated: list[dict[str, Any]] = []
    for item in source_items(data):
        channel = item["channel"]
        if channel == "小红书":
            target_dir = root / ASSET_ROOT / "xiaohongshu"
            paths = write_png(item, target_dir, XHS_SIZE, "xhs")
            generated.append({"id": item["id"], "channel": channel, "type": "cover", **paths})
            continue

        subdir = "douyin" if channel == "抖音" else "digital-human"
        target_dir = root / ASSET_ROOT / subdir
        paths = write_png(item, target_dir, VIDEO_SIZE, subdir)
        audio_path = target_dir / f"{slug(item['id'])}.mp3"
        video_path = target_dir / f"{slug(item['id'])}.mp4"
        if overwrite or not audio_path.exists():
            await synthesize(item["copy"], audio_path)
        if overwrite or not video_path.exists():
            make_video(root / paths["png"], audio_path, video_path)
        generated.append(
            {
                "id": item["id"],
                "channel": channel,
                "type": "video",
                **paths,
                "audio": str(audio_path.relative_to(root)),
                "video": str(video_path.relative_to(root)),
                "probe": probe_summary(video_path),
            }
        )

    manifest = {
        "updatedAt": data["updatedAt"],
        "source": str(source),
        "profile": {
            "voice": DEFAULT_VOICE,
            "rate": DEFAULT_RATE,
            "pitch": DEFAULT_PITCH,
            "audio": "24000Hz mono mp3",
            "video": "1080x1920 h264/aac for Douyin and digital human",
            "xiaohongshuCover": "1242x1660 png",
        },
        "assets": generated,
        "compliance": compliance_items(data),
    }
    manifest_path = root / ASSET_ROOT / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate VoiceHealth social promotion assets.")
    parser.add_argument(
        "--source",
        default=str(DEFAULT_SOURCE),
        help="JSON source with readyToPublish or items list",
    )
    parser.add_argument("--overwrite", action="store_true", help="Regenerate audio/video even if files exist")
    args = parser.parse_args()
    manifest = asyncio.run(generate_assets(source=Path(args.source), overwrite=args.overwrite))
    print(json.dumps({k: v for k, v in manifest.items() if k != "assets"}, ensure_ascii=False, indent=2))
    for item in manifest["assets"]:
        print(item["id"], item["channel"], item["type"])


if __name__ == "__main__":
    main()
