#!/usr/bin/env python3
"""Expand the 30-day content calendar into a publish-ready social queue."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from course_audio_pipeline import repo_root


DEFAULT_SOURCE = Path("data/marketing/content_calendar_30d.json")
DEFAULT_OUTPUT = Path("data/marketing/publish_queue_30d.json")
DEFAULT_OVERRIDES = Path("data/marketing/publish_queue_9d.json")

COMPLIANCE = [
    "不使用治愈率、有效率、确诊、筛查疾病、替代体检等承诺性表达",
    "不使用医生、专家、患者见证作为广告推荐",
    "不制造健康恐惧，不暗示不使用产品会患病或加重疾病",
    "数字人、合成语音、AI生成视频必须显著标注AI生成或AI数字人",
    "任何声音、面部、视频数据采集前必须取得用户授权",
    "所有页面保留健康管理参考和非诊断声明",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads((repo_root() / path).read_text(encoding="utf-8"))


def channel_id(channel: str, count: int) -> str:
    prefix = {"小红书": "xhs", "抖音": "dy", "数字人": "avatar"}[channel]
    return f"{prefix}-{count:03d}"


def tags_for(item: dict[str, Any]) -> list[str]:
    text = f"{item['title']} {item['hook']}"
    tags = ["声音健康", "健康管理"]
    if "睡眠" in text or "熬夜" in text:
        tags.append("睡眠管理")
    if "压力" in text or "办公室" in text:
        tags.append("压力管理")
    if "运动" in text:
        tags.append("运动健康")
    if "饮水" in text or "嗓音" in text or "咽" in text:
        tags.append("嗓音管理")
    if "家庭" in text or "父母" in text:
        tags.append("家庭健康")
    if "API" in text or "B端" in text or "商业" in text or "机构" in text:
        tags.append("商业合作")
    if "课程" in text or "学院" in text:
        tags.append("健康学院")
    if item["channel"] == "数字人":
        tags.append("AI数字人")
    else:
        tags.append("AI健康")
    return tags[:5]


def first_comment(item: dict[str, Any]) -> str:
    text = f"{item['title']} {item['hook']}"
    if "运动" in text:
        return "运动后如果持续胸痛、气短、头晕或明显不适，请优先寻求医疗帮助。"
    if "嗓音" in text or "咽" in text:
        return "如果持续声音嘶哑、吞咽困难或明显不适，请及时咨询专业医生。"
    if "确诊" in text or "治愈" in text or "边界" in text or "合规" in text:
        return "本内容只做健康管理参考，不构成医学诊断、治疗或用药建议。"
    if "B端" in text or "API" in text or "商业" in text or "机构" in text:
        return "商务试点需完成合规审查、数据授权、隐私告知和场景边界确认。"
    return "建议连续记录趋势，不要把单次分数当成健康结论。明显不适请及时就医。"


def xhs_copy(item: dict[str, Any]) -> tuple[str, str, str]:
    copy = (
        f"{item['title']}。{item['hook']}。我的做法是固定时间、固定文本、固定环境录30秒，"
        "再把声音趋势和睡眠、饮食、运动、压力打卡放在一起复盘。"
        "这不是诊断，也不替代体检；更像一个帮助自己发现生活方式影响的健康日记。"
    )
    cover = f"{item['hook']}。固定时间录30秒，再和睡眠、饮食、运动、压力一起看趋势。"
    caption = (
        f"{item['hook']}。我会把它当成健康管理参考，而不是疾病判断。"
        "连续记录比偶尔测一次更有价值。"
    )
    return copy, cover, caption


def douyin_copy(item: dict[str, Any]) -> tuple[str, str, str]:
    copy = (
        f"开场：{item['hook']}。镜头一：打开 VoiceHealth，按提示朗读30秒。"
        "镜头二：查看语速、停顿、能量和音质趋势。镜头三：结合睡眠、饮食、运动和压力打卡复盘。"
        "结尾：这不是诊断，是帮助你更早做生活方式调整的健康管理参考。"
    )
    cover = f"{item['hook']}。30秒朗读后看语速、停顿、能量和音质趋势。"
    caption = f"{item['title']}：先记录，再复盘。结果只用于健康管理参考，不替代医生和体检。"
    return copy, cover, caption


def avatar_copy(item: dict[str, Any]) -> tuple[str, str, str]:
    copy = (
        f"大家好，我是 VoiceHealth AI 数字健康助手。本视频由 AI 数字人生成。"
        f"今天讲的是：{item['title']}。{item['hook']}。"
        "VoiceHealth 更适合做趋势观察和生活方式复盘，不用于医学诊断、治疗或急症判断。"
        "如果出现明显不适，请及时咨询专业医生。"
    )
    cover = f"AI数字人生成。{item['hook']}。内容仅供健康管理参考。"
    caption = f"AI数字人科普：{item['title']}。内容仅用于健康管理参考。"
    return copy, cover, caption


def enrich_item(item: dict[str, Any], count: int) -> dict[str, Any]:
    builders = {"小红书": xhs_copy, "抖音": douyin_copy, "数字人": avatar_copy}
    copy, cover, caption = builders[item["channel"]](item)
    return {
        "id": channel_id(item["channel"], count),
        "day": item["day"],
        "channel": item["channel"],
        "format": item["format"],
        "title": item["title"],
        "hook": item["hook"],
        "copy": copy,
        "coverCopy": cover,
        "caption": caption,
        "cta": item["cta"],
        "firstComment": first_comment(item),
        "tags": tags_for(item),
    }


def load_overrides(path: Path) -> dict[int, dict[str, Any]]:
    target = repo_root() / path
    if not target.exists():
        return {}
    data = json.loads(target.read_text(encoding="utf-8"))
    return {item["day"]: item for item in data.get("items", [])}


def build(source: Path, output: Path, overrides: Path | None = DEFAULT_OVERRIDES) -> dict[str, Any]:
    data = load_json(source)
    override_items = load_overrides(overrides) if overrides else {}
    counts: defaultdict[str, int] = defaultdict(int)
    items = []
    for raw_item in data["items"]:
        counts[raw_item["channel"]] += 1
        override = override_items.get(raw_item["day"])
        if override:
            items.append(override)
        else:
            items.append(enrich_item(raw_item, counts[raw_item["channel"]]))

    payload = {
        "updatedAt": data["updatedAt"],
        "campaign": f"{data['campaign']} · 发布执行版",
        "source": str(source),
        "positioning": "AI声音健康管理参考平台，用30秒语音建立个人状态基线，联动睡眠、饮食、运动和压力打卡，不用于医学诊断或治疗。",
        "items": items,
        "compliance": COMPLIANCE,
    }
    target = repo_root() / output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a publish-ready VoiceHealth social queue.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--overrides", default=str(DEFAULT_OVERRIDES))
    args = parser.parse_args()
    payload = build(Path(args.source), Path(args.output), Path(args.overrides) if args.overrides else None)
    print(json.dumps({"items": len(payload["items"]), "output": args.output}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
