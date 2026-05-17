#!/usr/bin/env python3
"""Create natural 150-230 character spoken scripts for health courses.

If DEEPSEEK_API_KEY is present, the script calls DeepSeek Chat. Without a key,
it falls back to a conservative local condensation based on title, subtitle, and
content so the pipeline remains usable in local development.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

import httpx


DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data.get("courses"), list):
        raise ValueError(f"{path} must contain a courses array")
    return data


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def trim_to_sentence(text: str, min_chars: int = 150, max_chars: int = 230) -> str:
    compact = re.sub(r"\s+", "", text).strip()
    if len(compact) <= max_chars:
        return compact
    clipped = compact[:max_chars]
    for mark in ("。", "！", "？", "；"):
        pos = clipped.rfind(mark)
        if pos >= min_chars:
            return clipped[: pos + 1]
    return clipped


def local_spoken_script(course: dict[str, Any]) -> str:
    title = str(course.get("title", "本课")).strip()
    subtitle = str(course.get("subtitle", "")).strip()
    content = str(course.get("content", "")).strip()
    practice = str(course.get("practice", "")).strip()
    draft = (
        f"这一课我们学习{title}。{subtitle}。核心不是背知识点，而是把健康信息转成每天能执行的动作。"
        f"{content} 学完后，请完成一个小练习：{practice} 请把结果当作健康管理参考，持续观察趋势。"
    )
    return trim_to_sentence(draft)


def deepseek_spoken_script(course: dict[str, Any], api_key: str, model: str) -> str:
    title = str(course.get("title", "")).strip()
    subtitle = str(course.get("subtitle", "")).strip()
    content = str(course.get("content", "")).strip()
    practice = str(course.get("practice", "")).strip()
    prompt = f"""
请为健康教育小程序课程写一段中文自然口播导入稿。

要求：
- 150到230个中文字符左右。
- 听起来像老师在讲课，不像网页逐字朗读。
- 保持健康管理参考定位，不做诊断、治疗承诺。
- 语气稳重、清楚、可直接给 TTS 朗读。
- 不要使用标题、项目符号或英文缩写解释。

课程标题：{title}
副标题：{subtitle}
课程要点：{content}
行动练习：{practice}
""".strip()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是严谨的中文健康教育课程口播编辑。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
    }
    with httpx.Client(timeout=45) as client:
        response = client.post(DEEPSEEK_URL, headers=headers, json=payload)
        response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]
    return trim_to_sentence(text)


def enhance_catalog(input_path: Path, output_path: Path, model: str, force: bool) -> None:
    data = load_json(input_path)
    api_key = os.getenv("DEEPSEEK_API_KEY")
    for course in data["courses"]:
        if course.get("spokenScript") and not force:
            continue
        course["spokenScript"] = (
            deepseek_spoken_script(course, api_key, model) if api_key else local_spoken_script(course)
        )
    save_json(output_path, data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Enhance health course JSON with TTS-ready spoken scripts.")
    parser.add_argument("--input", required=True, help="输入课程 JSON")
    parser.add_argument("--output", required=True, help="输出增强后的课程 JSON")
    parser.add_argument("--model", default=os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument("--force", action="store_true", help="覆盖已有 spokenScript")
    args = parser.parse_args()
    enhance_catalog(Path(args.input), Path(args.output), args.model, args.force)
    print(f"enhanced course catalog written to {args.output}")


if __name__ == "__main__":
    main()
