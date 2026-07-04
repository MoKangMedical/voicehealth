#!/usr/bin/env python3
"""Check VoiceHealth WeChat mini program launch readiness."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


ROOT = Path(__file__).resolve().parents[1]
MINI_ROOT = ROOT / "voiceHealth-miniprogram-v2"
MP_ROOT = MINI_ROOT / "miniprogram"


@dataclass
class CheckResult:
    status: str
    title: str
    detail: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def add(results: list[CheckResult], status: str, title: str, detail: str) -> None:
    results.append(CheckResult(status=status, title=title, detail=detail))


def has_all(text: str, needles: Iterable[str]) -> bool:
    return all(needle in text for needle in needles)


def extract_js_string(text: str, key: str) -> Optional[str]:
    match = re.search(rf"{re.escape(key)}\s*:\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1) if match else None


def check_project_config(results: list[CheckResult]) -> None:
    path = MINI_ROOT / "project.config.json"
    if not path.exists():
      add(results, "FAIL", "小程序项目配置", f"缺少 {path.relative_to(ROOT)}")
      return

    try:
        config = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        add(results, "FAIL", "小程序项目配置", f"JSON 解析失败: {exc}")
        return

    appid = config.get("appid", "")
    if re.fullmatch(r"wx[a-zA-Z0-9]{16,32}", appid):
        add(results, "PASS", "真实 AppID", f"project.config.json appid={appid}")
    else:
        add(results, "FAIL", "真实 AppID", "请在 project.config.json 填入微信公众平台真实 AppID")

    root = config.get("miniprogramRoot", "")
    if root == "miniprogram/":
        add(results, "PASS", "小程序根目录", "miniprogramRoot=miniprogram/")
    else:
        add(results, "WARN", "小程序根目录", f"当前 miniprogramRoot={root!r}，请确认开发者工具导入正确")


def check_miniprogram_config(results: list[CheckResult]) -> str:
    path = MP_ROOT / "config.js"
    if not path.exists():
        add(results, "FAIL", "运行配置", f"缺少 {path.relative_to(ROOT)}")
        return "https://voicehealth.ai"

    text = read_text(path)
    base_url = extract_js_string(text, "baseUrl") or "https://voicehealth.ai"
    dev_url = extract_js_string(text, "devBaseUrl") or ""

    if base_url.startswith("https://"):
        add(results, "PASS", "生产 API 域名", f"baseUrl={base_url}")
    else:
        add(results, "FAIL", "生产 API 域名", "baseUrl 必须使用 HTTPS 域名")

    if dev_url.startswith(("http://127.0.0.1", "http://localhost", "http://192.168.")):
        add(results, "PASS", "开发 API 地址", f"devBaseUrl={dev_url}")
    else:
        add(results, "WARN", "开发 API 地址", f"当前 devBaseUrl={dev_url or '未配置'}")

    if has_all(text, ["getMiniProgramEnvVersion", "envVersion === 'develop'", "useDev: useDevApi"]):
        add(results, "PASS", "环境自动切换", "开发版走 devBaseUrl，体验版/正式版走 baseUrl")
    elif "useDev: true" in text:
        add(results, "FAIL", "环境自动切换", "config.js 仍固定 useDev: true，正式版会误连本地 API")
    else:
        add(results, "WARN", "环境自动切换", "未识别到标准自动切换逻辑，请人工复核")

    return base_url


def check_recording_flow(results: list[CheckResult]) -> None:
    app_js = MP_ROOT / "app.js"
    index_js = MP_ROOT / "pages" / "index" / "index.js"
    app_json = MP_ROOT / "app.json"

    if app_js.exists() and has_all(read_text(app_js), ["getApiBaseUrl", "wx.uploadFile", "X-User-Id"]):
        add(results, "PASS", "上传封装", "app.js 已封装鉴权 uploadFile")
    else:
        add(results, "FAIL", "上传封装", "app.js 需要封装 wx.uploadFile 并带用户身份")

    if index_js.exists() and has_all(read_text(index_js), ["wx.getRecorderManager", "/api/v1/voice/analyze", "reading_text_id"]):
        add(results, "PASS", "语音健康分析入口", "首页已接入录音、朗读文本和 /api/v1/voice/analyze")
    else:
        add(results, "FAIL", "语音健康分析入口", "首页需要接入录音和 /api/v1/voice/analyze")

    if app_json.exists() and "scope.record" in read_text(app_json):
        add(results, "PASS", "麦克风权限说明", "app.json 已声明 scope.record 用途")
    else:
        add(results, "FAIL", "麦克风权限说明", "app.json 缺少 scope.record 权限说明")

    privacy = MP_ROOT / "pages" / "privacy" / "privacy.wxml"
    if privacy.exists() and has_all(read_text(privacy), ["隐私政策", "录音", "不构成医学诊断"]):
        add(results, "PASS", "隐私与非诊断声明", "隐私页覆盖录音数据和健康参考边界")
    else:
        add(results, "FAIL", "隐私与非诊断声明", "隐私页需要明确录音数据用途和非诊断声明")


def check_backend_routes(results: list[CheckResult]) -> None:
    routes = ROOT / "src" / "api" / "routes.py"
    main = ROOT / "src" / "api" / "main.py"
    if routes.exists() and has_all(read_text(routes), ['@router.post("/voice/analyze")', '@router.get("/verification/text")', '@router.get("/health")']):
        add(results, "PASS", "后端 API 路由", "已提供语音分析、朗读文本和 /api/v1/health")
    else:
        add(results, "FAIL", "后端 API 路由", "缺少生产小程序所需后端路由")

    if main.exists() and '@app.get("/api/health")' in read_text(main):
        add(results, "PASS", "兼容健康检查", "已提供 /api/health 供反向代理和监控探测")
    else:
        add(results, "WARN", "兼容健康检查", "建议保留 /api/health")


def check_docs(results: list[CheckResult]) -> None:
    launch_doc = ROOT / "docs" / "WECHAT_MINIPROGRAM_LAUNCH.md"
    setup_doc = ROOT / "WECHAT_MINIPROGRAM_SETUP.md"
    if launch_doc.exists() and has_all(read_text(launch_doc), ["微信公众平台", "合法域名", "语音健康分析"]):
        add(results, "PASS", "上线操作文档", "docs/WECHAT_MINIPROGRAM_LAUNCH.md 已覆盖发布流程")
    else:
        add(results, "FAIL", "上线操作文档", "缺少微信上线发布清单")

    if setup_doc.exists() and "体验版和正式版" in read_text(setup_doc):
        add(results, "PASS", "配置说明", "WECHAT_MINIPROGRAM_SETUP.md 已说明自动环境切换")
    else:
        add(results, "WARN", "配置说明", "建议更新 WECHAT_MINIPROGRAM_SETUP.md 的生产配置说明")


def fetch_json(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VoiceHealthLaunchCheck/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read(4096).decode("utf-8", errors="replace")
            if response.status < 200 or response.status >= 300:
                return False, f"HTTP {response.status}"
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                return False, "响应不是 JSON"
            if payload.get("service") == "VoiceHealth" and payload.get("status") == "healthy":
                return True, "VoiceHealth healthy"
            return False, f"JSON 不像 VoiceHealth 健康检查: {body[:120]}"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def check_live_domain(results: list[CheckResult], api_base: str, strict: bool) -> None:
    base = api_base.rstrip("/")
    if not base.startswith("https://"):
        add(results, "FAIL", "线上域名连通", "线上小程序必须使用 HTTPS API 域名")
        return

    ok_v1, detail_v1 = fetch_json(f"{base}/api/v1/health")
    ok_compat, detail_compat = fetch_json(f"{base}/api/health")
    if ok_v1 and ok_compat:
        add(results, "PASS", "线上域名连通", f"{base} 的 /api/v1/health 和 /api/health 均正常")
        return

    status = "FAIL" if strict else "WARN"
    add(
        results,
        status,
        "线上域名连通",
        f"{base} 尚未确认绑定 VoiceHealth API；/api/v1/health={detail_v1}; /api/health={detail_compat}",
    )


def print_results(results: list[CheckResult]) -> None:
    order = {"FAIL": 0, "WARN": 1, "PASS": 2}
    for item in sorted(results, key=lambda r: (order.get(r.status, 9), r.title)):
        print(f"[{item.status}] {item.title}: {item.detail}")

    counts = {status: sum(1 for item in results if item.status == status) for status in ("PASS", "WARN", "FAIL")}
    print(f"\nSummary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check WeChat mini program launch readiness.")
    parser.add_argument("--api-base", default="", help="Production API base URL. Defaults to miniprogram config baseUrl.")
    parser.add_argument("--skip-live", action="store_true", help="Skip live HTTPS health checks.")
    parser.add_argument("--strict-live", action="store_true", help="Treat failed live domain checks as launch-blocking.")
    args = parser.parse_args()

    results: list[CheckResult] = []
    check_project_config(results)
    config_base = check_miniprogram_config(results)
    check_recording_flow(results)
    check_backend_routes(results)
    check_docs(results)

    api_base = args.api_base or config_base
    if not args.skip_live:
        check_live_domain(results, api_base, args.strict_live)

    print_results(results)
    return 1 if any(item.status == "FAIL" for item in results) else 0


if __name__ == "__main__":
    sys.exit(main())
