#!/usr/bin/env python3
"""
pipeline_orchestrator.py — 统一批处理编排器

功能：
  读取 items.json（支持 url / urls 两种格式），
  自动按来源（夸克/百度）分流，分别转存+分享，
  按资源名合并结果后统一触发发布流程。

Version: 1.1.0

用法：
  python /path/to/pipeline_orchestrator.py \\
    --items-json /path/to/items.json \\
    --label "短裤哥批次"

items.json 格式（支持单链接和多链接）：
  [
    {
      "title": "樊登讲书2026年合集",
      "urls": [
        "https://pan.quark.cn/s/xxx",
        "https://pan.baidu.com/s/xxx?pwd=xxx"
      ]
    },
    {
      "title": "泰坦尼克号",
      "url": "https://pan.quark.cn/s/xxx"
    }
  ]

  旧格式（单 url）和数组格式（urls）可混用。

依赖：
  - QuarkPanTool/quark_batch_run.py
  - QuarkPanTool/baidu_batch_run.py
  - scripts/copy_promo_to_folders.py
  - scripts/mswnlz_publish.py
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs

# ─── 路径 ────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
QUARKPANTOOL_DIR = SCRIPT_DIR.parent.parent.parent / "QuarkPanTool"
SCRIPTS_DIR = SCRIPT_DIR

PYTHON = sys.executable
VENV_PYTHON = str(QUARKPANTOOL_DIR / ".venv" / "bin" / "python")


# ─── URL 工具 ────────────────────────────────

def detect_source(url: str) -> str:
    """检测网盘来源：quark / baidu / unknown"""
    url_lower = url.lower()
    if "pan.quark.cn" in url_lower:
        return "quark"
    elif "pan.baidu.com" in url_lower:
        return "baidu"
    else:
        return "unknown"


def extract_pwd(baidu_url: str) -> str:
    """从百度链接提取提取码"""
    parsed = urlparse(baidu_url)
    qs = parse_qs(parsed.query)
    return qs.get("pwd", [""])[0]


def normalize_items(items_raw: list) -> list:
    """标准化 items：确保每个 item 都有 title 和 urls（列表）"""
    result = []
    for it in items_raw:
        title = (it.get("title") or "").strip()
        if not title:
            title = (it.get("name") or "").strip()
        if not title:
            continue  # 没标题的跳过

        # 支持 url（单字符串）和 urls（数组）
        urls = it.get("urls")
        if urls is None and it.get("url"):
            urls = [it["url"]]
        if urls is None and it.get("input_url"):
            urls = [it["input_url"]]
        if not urls:
            continue

        # 去重、过滤无用链接
        seen = set()
        clean_urls = []
        for u in urls:
            u = u.strip()
            if u and u not in seen and detect_source(u) != "unknown":
                seen.add(u)
                clean_urls.append(u)

        if not clean_urls:
            continue

        result.append({
            "title": title,
            "urls": clean_urls,
        })

    return result


# ─── 分流 ────────────────────────────────────

def split_by_source(items: list) -> Tuple[list, list]:
    """将资源按网盘来源拆分为两份"""
    quark_items = []
    baidu_items = []

    for item in items:
        title = item["title"]
        for url in item["urls"]:
            source = detect_source(url)
            if source == "quark":
                quark_items.append({"title": title, "url": url})
            elif source == "baidu":
                baidu_items.append({"title": title, "url": url})

    return quark_items, baidu_items


# ─── 子进程执行 ──────────────────────────────

def run_script(
    cmd: list,
    cwd: str,
    label: str = "",
    timeout: int = 480,
) -> dict:
    """执行一个外部脚本，返回结构化结果"""
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{QUARKPANTOOL_DIR}:{env.get('PYTHONPATH', '')}"

    print(f"\n{'='*60}")
    print(f"[{label}] 执行: {' '.join(cmd)}")
    print(f"[{label}] 目录: {cwd}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        print(f"[{label}] ❌ 超时 ({timeout}s)")
        return {"success": False, "error": "timeout", "stdout": "", "stderr": ""}
    except Exception as e:
        print(f"[{label}] ❌ 执行异常: {e}")
        return {"success": False, "error": str(e), "stdout": "", "stderr": ""}

    if result.returncode == 0:
        print(f"[{label}] ✅ 完成")
        if result.stdout:
            print(result.stdout[:2000])
    else:
        print(f"[{label}] ❌ 失败 (code={result.returncode})")
        if result.stderr:
            print(result.stderr[:2000])

    return {
        "success": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


# ─── 合并结果 ────────────────────────────────

def merge_results(
    quark_result_path: Optional[Path],
    baidu_result_path: Optional[Path],
    batch_folder_name: str,
    items_normalized: list,
) -> dict:
    """按资源名合并两个网盘的分享结果"""
    quark_urls: Dict[str, str] = {}   # original_title -> share_url
    baidu_urls: Dict[str, str] = {}   # original_title -> share_url

    # 读取夸克结果（用 items 数组中的原始标题匹配 share_results）
    if quark_result_path and quark_result_path.exists():
        with open(quark_result_path, encoding="utf-8") as f:
            data = json.load(f)
        items_meta = data.get("items", [])
        srs = data.get("share_results", [])
        for idx, sr in enumerate(srs):
            orig_title = ""
            if idx < len(items_meta):
                orig_title = items_meta[idx].get("title", "")
            name = sr.get("name", "")
            url = sr.get("share_url", "")
            key = orig_title or name
            if key:
                quark_urls[key] = url

    # 读取百度结果
    if baidu_result_path and baidu_result_path.exists():
        with open(baidu_result_path, encoding="utf-8") as f:
            data = json.load(f)
        items_meta = data.get("items", [])
        srs = data.get("share_results", [])
        for idx, sr in enumerate(srs):
            orig_title = ""
            if idx < len(items_meta):
                orig_title = items_meta[idx].get("title", "")
            name = sr.get("name", "")
            url = sr.get("share_url", "")
            key = orig_title or name
            if key:
                baidu_urls[key] = url

    merged = []
    for item in items_normalized:
        title = item["title"]

        # 最多尝试两种匹配：原始标题 / 名字前缀匹配
        def _find(store: dict, fallback_key: str = "") -> str:
            # 精确匹配原始标题
            if title in store:
                return store[title]
            # 精确匹配 fallback
            if fallback_key and fallback_key in store:
                return store[fallback_key]
            # 前缀匹配
            for k, v in store.items():
                if k and (title.startswith(k) or k.startswith(title)):
                    return v
            return ""

        quark_url = _find(quark_urls)
        baidu_url = _find(baidu_urls)

        links = {}
        if quark_url:
            links["quark"] = quark_url
        if baidu_url:
            links["baidu"] = baidu_url

        if not links:
            print(f"  ⚠️ {title}: 两个网盘均未找到分享结果")
            continue

        entry = {
            "name": title,
            "title": title,
            "links": links,
            "share_url": quark_url or baidu_url,  # 优先夸克
        }
        merged.append(entry)

        url_count = len(links)
        sources_str = " + ".join(links.keys())
        print(f"  [{url_count}链接] {title}: {sources_str}")

    # 从任意一个存在的源文件获取月份和批次信息
    month = ""
    if quark_result_path and quark_result_path.exists():
        with open(quark_result_path) as f:
            month = json.load(f).get("month", "")
    if not month and baidu_result_path and baidu_result_path.exists():
        with open(baidu_result_path) as f:
            month = json.load(f).get("month", "")

    return {
        "source": "combined",
        "month": month or datetime.now().strftime("%Y%m"),
        "batch_folder_name": batch_folder_name,
        "items": items_normalized,
        "share_results": merged,
    }


# ─── 创建临时 items.json 文件 ──────────────

def write_temp_items(items: list, suffix: str) -> Path:
    """写一份仅包含该网盘链接的临时 items.json"""
    tmp = SCRIPTS_DIR / f"items_{suffix}.json"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return tmp


# ─── 主入口 ──────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="统一批处理编排器 v1.1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--items-json", required=True, help="items.json 路径")
    ap.add_argument("--label", default="短裤哥批次", help="批次标签")
    ap.add_argument("--month", default="", help="月份（如 202607）")
    ap.add_argument("--out-json", default="", help="合并后的输出路径（默认自动）")
    ap.add_argument("--dry-run", action="store_true", help="模拟运行：跳过TG通知和GitHub发布")
    args = ap.parse_args()

    # ── 1. 读取 & 标准化 ──
    print(f"\n{'='*60}")
    print("📋 读取 items.json...")
    items_raw = json.loads(Path(args.items_json).read_text(encoding="utf-8"))
    norm_items = normalize_items(items_raw)
    print(f"   共 {len(norm_items)} 个资源")
    for it in norm_items:
        sources = ", ".join(detect_source(u) for u in it["urls"])
        print(f"   • {it['title']} ({sources})")

    if not norm_items:
        print("❌ 没有有效资源，退出")
        return

    # ── 2. 分流 ──
    quark_items, baidu_items = split_by_source(norm_items)
    print(f"\n   夸克: {len(quark_items)} 个链接")
    print(f"   百度: {len(baidu_items)} 个链接")

    # ── 3. 生成批次信息 ──
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    batch_folder_name = f"{ts}_{args.label}"
    month = args.month or datetime.now().strftime("%Y%m")

    # ── 4. 执行 A 段（转存+分享） ──
    quark_result_path: Optional[Path] = None
    baidu_result_path: Optional[Path] = None

    if quark_items:
        print(f"\n{'#'*60}")
        print(f"# 夸克 A 段：{len(quark_items)} 个链接")
        print(f"{'#'*60}")
        quark_items_file = write_temp_items(quark_items, "quark")
        quark_out = SCRIPTS_DIR / f"batch_share_results_quark.json"

        result = run_script(
            [
                VENV_PYTHON,
                str(SCRIPTS_DIR / "quark_batch_run.py"),
                "--items-json", str(quark_items_file),
                "--label", args.label,
                "--month", month,
                "--out-json", str(quark_out),
            ],
            cwd=str(QUARKPANTOOL_DIR),
            label="夸克A段",
        )

        if result["success"]:
            quark_result_path = quark_out
        else:
            print("  ⚠️ 夸克 A 段执行失败，继续处理百度")

        # 删除临时文件
        quark_items_file.unlink(missing_ok=True)

    if baidu_items:
        print(f"\n{'#'*60}")
        print(f"# 百度 A 段：{len(baidu_items)} 个链接")
        print(f"{'#'*60}")
        baidu_items_file = write_temp_items(baidu_items, "baidu")
        baidu_out = SCRIPTS_DIR / f"batch_share_results_baidu.json"

        result = run_script(
            [
                PYTHON,
                str(QUARKPANTOOL_DIR / "baidu_batch_run.py"),
                "--items-json", str(baidu_items_file),
                "--label", args.label,
                "--month", month,
                "--out-json", str(baidu_out),
            ],
            cwd=str(QUARKPANTOOL_DIR),
            label="百度A段",
        )

        if result["success"]:
            baidu_result_path = baidu_out
        else:
            print("  ⚠️ 百度 A 段执行失败")

        baidu_items_file.unlink(missing_ok=True)

    # ── 5. 合并结果 ──
    print(f"\n{'#'*60}")
    print(f"# 合并结果")
    print(f"{'#'*60}")

    merged = merge_results(
        quark_result_path,
        baidu_result_path,
        batch_folder_name,
        norm_items,
    )

    if not merged["share_results"]:
        print("❌ 没有成功分享的资源，退出")
        return

    merged_path = Path(args.out_json) if args.out_json else (SCRIPTS_DIR / "batch_share_results.json")
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 合并结果已保存: {merged_path}")
    print(f"   共 {len(merged['share_results'])} 条，其中：")
    dual_count = sum(1 for sr in merged["share_results"] if len(sr.get("links", {})) > 1)
    single_count = len(merged["share_results"]) - dual_count
    print(f"   • 双链接: {dual_count}")
    print(f"   • 单链接: {single_count}")

    # ── 6. B 段：复制推广文件 ──
    # 夸克部分
    if quark_result_path and quark_result_path.exists():
        print(f"\n{'#'*60}")
        print(f"# 夸克推广文件复制")
        print(f"{'#'*60}")
        run_script(
            [
                VENV_PYTHON,
                str(SCRIPTS_DIR / "copy_promo_to_folders.py"),
                "--batch-json", str(quark_result_path),
            ],
            cwd=str(QUARKPANTOOL_DIR),
            label="夸克推广",
        )

    # 百度部分
    if baidu_result_path and baidu_result_path.exists():
        print(f"\n{'#'*60}")
        print(f"# 百度推广文件复制")
        print(f"{'#'*60}")
        run_script(
            [
                PYTHON,
                str(SCRIPTS_DIR / "copy_promo_to_folders.py"),
                "--batch-json", str(baidu_result_path),
            ],
            cwd=str(QUARKPANTOOL_DIR),
            label="百度推广",
        )

    # ── 7. 发布（仅非 dry-run）──
    if not args.dry_run:
        print(f"\n{'#'*60}")
        print(f"# 发布（GitHub + TG通知 + 站点重建）")
        print(f"{'#'*60}")

        run_script(
            [
                PYTHON,
                str(SCRIPTS_DIR / "mswnlz_publish.py"),
                "--month", merged["month"],
                "--batch-json", str(merged_path),
            ],
            cwd=str(QUARKPANTOOL_DIR),
            label="发布",
        )
    else:
        print(f"\n{'#'*60}")
        print(f"# [dry-run] 跳过发布")
        print(f"{'#'*60}")
        print(f"   合并结果已保存: {merged_path}")
        print(f"   共 {len(merged['share_results'])} 条")
        print(f"   用以下命令手动发布：")
        print(f"     python3 {SCRIPTS_DIR / 'mswnlz_publish.py'} --month {merged['month']} --batch-json {merged_path}")

    # ── 8. 清理临时文件 ──
    for tmp in [SCRIPTS_DIR / "batch_share_results_quark.json",
                SCRIPTS_DIR / "batch_share_results_baidu.json"]:
        if tmp.exists():
            tmp.unlink()

    print(f"\n{'='*60}")
    print(f"✅ 全部完成！")
    print(f"   处理 {len(norm_items)} 个资源")
    print(f"   成功发布 {len(merged['share_results'])} 条")
    print(f"   输出: {merged_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
