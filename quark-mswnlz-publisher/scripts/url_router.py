"""url_router.py — 网盘链接类型自动路由

根据 URL 自动判断是夸克还是百度，返回路由信息。
Version: 1.0.0
"""

import re


def route_url(url: str) -> str:
    """判断网盘类型

    Args:
        url: 网盘分享链接

    Returns:
        "quark" | "baidu"

    Raises:
        ValueError: 不支持的网盘类型
    """
    url = url.strip().lower()

    if "quark.cn" in url or "pan.quark.cn" in url:
        return "quark"

    if "pan.baidu.com" in url or "yun.baidu.com" in url:
        return "baidu"

    raise ValueError(f"不支持的网盘类型: {url[:50]}...")


def detect_and_run(items_json: str, out_json: str, label: str = "短裤哥批次",
                   month: str = ""):
    """统一入口：自动检测网盘类型并执行对应流程

    items.json 格式:
      [{"title": "xxx", "url": "https://pan.xxx.com/s/..."}]

    支持混合类型（每个 item 独立判断）
    """
    import json
    from pathlib import Path

    items = json.loads(Path(items_json).read_text(encoding="utf-8"))
    if not items:
        print("[ROUTER] ⚠️ 空的 items.json")
        return

    # 检查是否有多种类型
    types = set()
    for it in items:
        url = it.get("url", "")
        if url:
            try:
                types.add(route_url(url))
            except ValueError:
                pass

    if len(types) > 1:
        print(f"[ROUTER] ⚠️ 检测到混合类型: {types}")
        print("  当前不支持混合类型批量处理，请分开执行")
        return

    source = route_url(items[0]["url"])
    print(f"[ROUTER] 🔀 检测到: {source.upper()} 网盘链接")

    if source == "quark":
        # 走已有夸克流程
        import subprocess
        cmd = [
            "python", str(Path(__file__).resolve().parent / "quark_batch_run.py"),
            "--label", label,
            "--month", month or "",
            "--items-json", items_json,
            "--out-json", out_json,
        ]
        print(f"[ROUTER] 🚀 执行夸克流程...")
        subprocess.run(cmd, cwd=str(Path.cwd()))

    elif source == "baidu":
        # 走百度流程
        import subprocess
        cmd = [
            "python", str(Path(__file__).resolve().parent.parent.parent.parent
                         / "QuarkPanTool" / "baidu_batch_run.py"),
            "--label", label,
            "--items-json", items_json,
            "--out-json", out_json,
            "--month", month or "",
        ]
        work_dir = str(Path(__file__).resolve().parent.parent.parent.parent
                      / "QuarkPanTool")
        print(f"[ROUTER] 🚀 执行百度流程...")
        subprocess.run(cmd, cwd=work_dir)
