"""
cleanup_junk_files.py — 清理网盘资源文件夹内的垃圾文件（v2.0）

在全流程中的位置：A段 save → 🧹 这里 → share → promo_copy → 发布

v2.0 更新：
  - 🔁 递归扫描（默认6层深度），不再只扫一级
  - 🔑 多账号自动遍历：扫描 config/cookies*.txt 全部 cookie 文件
  - 📊 汇总输出每个账号的清理结果

工作方式：
  读取 batch_share_results.json → 遍历所有夸克 cookie 账号
  → 每个账号在根目录找批次文件夹 → 递归扫描所有子文件夹
  → 匹配垃圾文件名单（子串匹配）→ 删除

用法：
  cd /Users/m/document/QNSZ/project/QuarkPanTool
  .venv/bin/python /Users/m/document/QNSZ/project/skills/quark-mswnlz-publisher/scripts/cleanup_junk_files.py \\
      --batch-json batch_share_results.json \\
      --junk-config config/junk_files.json

参数：
  --junk-config: 垃圾文件名单配置（支持子串匹配）
  --quark-parent-fid: 夸克批次文件夹的父目录 FID（默认 0=根目录）
  --baidu-batch-path: 百度批次文件夹路径（如 /短裤哥批次）
  --max-depth: 递归扫描最大深度（默认 6）
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# ── 路径约定 ─────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent.parent / "QuarkPanTool"  # QuarkPanTool/
sys.path.insert(0, str(PROJECT_DIR))

from quark import QuarkPanFileManager
from baidu_client import BaiduPCSClient


def load_junk_config(path: str) -> list:
    """加载垃圾文件名列表"""
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    return cfg.get("files", [])


def match_junk(filename: str, junk_files: list) -> bool:
    """子串匹配：只要垃圾名单中有任意一个字符串是文件名的子串，就算匹配"""
    for junk in junk_files:
        if junk in filename:
            return True
    return False


async def get_quark_batch_folder_fid(mgr: QuarkPanFileManager, parent_fid: str, folder_name: str) -> str | None:
    """在 Quark 父目录中按名称精确查找批次文件夹的 FID"""
    page = 1
    size = 200
    while True:
        data = await mgr.get_sorted_file_list(
            pdir_fid=parent_fid, page=str(page), size=str(size), fetch_total="true"
        )
        lst = (data.get("data") or {}).get("list") or []
        meta = data.get("metadata") or {}
        for item in lst:
            if item.get("dir") and item.get("file_name") == folder_name:
                return item["fid"]
        total = meta.get("_total") or 0
        _size = meta.get("_size") or size
        _page = meta.get("_page") or page
        if _size * _page >= total:
            break
        page += 1
    return None


async def get_quark_folder_children(mgr: QuarkPanFileManager, folder_fid: str) -> list[dict]:
    """获取 Quark 文件夹下所有子项"""
    all_items = []
    page = 1
    size = 200
    while True:
        data = await mgr.get_sorted_file_list(
            pdir_fid=folder_fid, page=str(page), size=str(size), fetch_total="true"
        )
        lst = (data.get("data") or {}).get("list") or []
        meta = data.get("metadata") or {}
        all_items.extend(lst)
        total = meta.get("_total") or 0
        _size = meta.get("_size") or size
        _page = meta.get("_page") or page
        if _size * _page >= total:
            break
        page += 1
    return all_items


async def cleanup_quark_recursive(mgr: QuarkPanFileManager, folder_fid: str, junk_files: list,
                                   path: str = "", depth: int = 0, max_depth: int = 6) -> dict:
    """
    递归扫描文件夹，删除所有匹配垃圾名单的文件和子文件夹。

    v2.0: 不再只扫一级，而是递归到 max_depth 层。
    遇到垃圾文件夹时整个删除（不进入其内部继续扫描）。
    遇到正常文件夹时递归进入扫描。
    """
    summary = {"total_deleted": 0, "details": []}

    children = await get_quark_folder_children(mgr, folder_fid)

    # 分类：垃圾文件 / 垃圾文件夹 / 正常文件夹 / 正常文件
    junk_items = []
    normal_dirs = []

    for c in children:
        name = c.get("file_name", "")
        is_dir = c.get("dir", False)
        if match_junk(name, junk_files):
            junk_items.append(c)
        elif is_dir:
            normal_dirs.append(c)

    # 删除当前层级的垃圾
    if junk_items:
        fids = [c["fid"] for c in junk_items]
        names = [c.get("file_name", "?") for c in junk_items]
        try:
            await mgr.delete_files(fids, pdir_fid=folder_fid)
            summary["total_deleted"] += len(fids)
            for n in names:
                summary["details"].append(f"{path}/{n}")
                print(f"    🗑️ {path}/{n}")
        except Exception as e:
            print(f"    ❌ 删除失败 ({path}): {e}")

    # 递归进入正常子文件夹
    if depth < max_depth:
        for sd in normal_dirs:
            sub_name = sd.get("file_name", "?")
            sub_fid = sd["fid"]
            sub_summary = await cleanup_quark_recursive(
                mgr, sub_fid, junk_files, f"{path}/{sub_name}", depth + 1, max_depth
            )
            summary["total_deleted"] += sub_summary["total_deleted"]
            summary["details"].extend(sub_summary["details"])

    return summary


async def cleanup_quark_batch_folder(mgr: QuarkPanFileManager, batch_folder_fid: str,
                                      junk_files: list, max_depth: int = 6) -> dict:
    """扫描 Quark 批次文件夹，递归清理所有层级的垃圾文件"""
    summary = {"total_deleted": 0, "total_folders": 0, "folders_with_junk": [], "details": []}

    # 获取所有子文件夹（一级）
    children = await get_quark_folder_children(mgr, batch_folder_fid)
    subdirs = [c for c in children if c.get("dir")]
    summary["total_folders"] = len(subdirs)

    print(f"  📁 共 {len(subdirs)} 个一级子文件夹，递归 {max_depth} 层扫描")

    for sd in subdirs:
        sub_name = sd.get("file_name", "?")
        sub_fid = sd["fid"]
        print(f"\n  🔍 [{sub_name}]")
        sub_summary = await cleanup_quark_recursive(
            mgr, sub_fid, junk_files, sub_name, depth=0, max_depth=max_depth
        )
        if sub_summary["total_deleted"] > 0:
            summary["total_deleted"] += sub_summary["total_deleted"]
            summary["folders_with_junk"].append(sub_name)
            summary["details"].extend(sub_summary["details"])
        else:
            print(f"    ✅ 无垃圾文件")

    return summary


def cleanup_baidu_batch_folder(client: BaiduPCSClient, batch_path: str, junk_files: list) -> dict:
    """扫描 Baidu 批次文件夹下全部子文件夹，清理所有匹配的垃圾文件"""
    summary = {"total_deleted": 0, "total_folders": 0, "folders_with_junk": [], "details": []}

    entries = client.ls(batch_path)
    dirs = [e for e in entries if e.get("size", "").strip() == "-"]
    files = [e for e in entries if e.get("size", "").strip() not in ("", "-")]

    # 批次根目录下匹配垃圾名单的子文件夹（直接删整个文件夹）
    junk_dirs_at_root = [d for d in dirs if match_junk(d.get("name", ""), junk_files)]
    for jd in junk_dirs_at_root:
        full_path = f"{batch_path}/{jd['name']}"
        if client.rm(full_path):
            summary["total_deleted"] += 1
            summary["folders_with_junk"].append(jd["name"])
            summary["details"].append({"folder": "(根)", "deleted": [jd["name"]], "count": 1})
            print(f"    🗑️ [根] 删文件夹: {jd['name']}")

    normal_dirs = [d for d in dirs if not match_junk(d.get("name", ""), junk_files)]
    print(f"  📁 共 {len(normal_dirs)} 个子文件夹, {len(files)} 个文件")

    for sd in normal_dirs:
        sub_name = sd.get("name", "?")
        sub_path = f"{batch_path}/{sub_name}"
        sub_entries = client.ls(sub_path)
        sub_files = [f for f in sub_entries if f.get("size", "").strip() not in ("", "-")]

        deleted_names = []
        for f in sub_files:
            fname = f.get("name", "")
            if match_junk(fname, junk_files):
                full_path = f"{sub_path}/{fname}"
                if client.rm(full_path):
                    deleted_names.append(fname)
                    summary["total_deleted"] += 1

        if deleted_names:
            summary["folders_with_junk"].append(sub_name)
            summary["details"].append({
                "folder": sub_name, "deleted": deleted_names, "count": len(deleted_names)
            })
            print(f"    🗑️ [{sub_name}] 删 {len(deleted_names)} 个: {', '.join(deleted_names)}")
        else:
            print(f"    ✅ [{sub_name}] 无垃圾文件")

    summary["total_folders"] = len(dirs)
    return summary


async def cleanup_with_cookie(cookie_file: str, batch_folder_name: str, junk_files: list,
                               parent_fid: str = "0", max_depth: int = 6) -> dict:
    """用指定 cookie 文件登录并清理批次文件夹（v2.0 多账号支持）"""
    summary = {"total_deleted": 0, "folders_with_junk": [], "batch_found": False}
    label = Path(cookie_file).name
    print(f"\n  🔑 使用 {label}")
    try:
        mgr = QuarkPanFileManager(headless=True, slow_mo=0)
        # 覆盖 cookie
        cookies = Path(cookie_file).read_text(encoding="utf-8").strip()
        mgr.cookies = cookies
        mgr.headers["cookie"] = cookies

        batch_fid = await get_quark_batch_folder_fid(mgr, parent_fid, batch_folder_name)
        if not batch_fid:
            print(f"  ⚠️ {label}: 根目录找不到批次文件夹 '{batch_folder_name}'（此账号可能没有此批次）")
            return summary
        summary["batch_found"] = True
        print(f"  ✅ {label}: 找到批次 FID={batch_fid}")
        sub_summary = await cleanup_quark_batch_folder(mgr, batch_fid, junk_files, max_depth=max_depth)
        summary["total_deleted"] = sub_summary["total_deleted"]
        summary["folders_with_junk"] = sub_summary.get("folders_with_junk", [])
    except Exception as e:
        print(f"  ❌ {label} 清理出错: {e}")
    return summary


async def main():
    p = argparse.ArgumentParser(description="清理网盘资源文件夹内垃圾文件（v2.0 多账号+递归）")
    p.add_argument("--batch-json", required=True, help="batch_share_results.json 路径")
    p.add_argument("--junk-config", required=True, help="junk_files.json 路径")
    p.add_argument("--quark-parent-fid", default="0", help="夸克批次文件夹的父目录 FID")
    p.add_argument("--baidu-batch-path", default="/短裤哥批次", help="百度批次文件夹路径")
    p.add_argument("--max-depth", type=int, default=6, help="递归扫描最大深度（默认6）")
    args = p.parse_args()

    batch = json.loads(Path(args.batch_json).read_text(encoding="utf-8"))
    junk_files = load_junk_config(args.junk_config)

    print(f"\n🧹 垃圾文件清理 v2.0 ({len(junk_files)} 个模式, 递归 {args.max_depth} 层)")
    print(f"   模式: {', '.join(junk_files)}\n")

    # ── Quark 清理（遍历所有 cookie 文件）─────────────────
    batch_folder_name = batch.get("batch_folder_name", "")
    if batch_folder_name:
        print(f"\n☁️  Quark 清理 — 批次文件夹: {batch_folder_name}")
        config_dir = PROJECT_DIR / "config"
        # 查找所有 cookie 文件：cookies.txt, cookies_1.txt, cookies_2.txt, ...
        cookie_files = sorted(config_dir.glob("cookies*.txt"))
        cookie_files = [f for f in cookie_files if not str(f).endswith(".bak")]

        if not cookie_files:
            print("  ❌ 找不到任何 cookie 文件")
        else:
            print(f"  发现 {len(cookie_files)} 个 cookie 文件: {[f.name for f in cookie_files]}")
            grand_total = 0
            accounts_cleaned = 0
            for cf in cookie_files:
                result = await cleanup_with_cookie(
                    str(cf), batch_folder_name, junk_files,
                    args.quark_parent_fid, max_depth=args.max_depth
                )
                grand_total += result["total_deleted"]
                if result["batch_found"]:
                    accounts_cleaned += 1
            print(f"\n  📊 Quark 清理汇总: {accounts_cleaned}/{len(cookie_files)} 个账号有此批次, 共删 {grand_total} 个垃圾文件")

    # ── Baidu 清理 ──────────────────────────────────────
    baidu_batch = args.baidu_batch_path
    print(f"\n☁️  Baidu 清理 — 批次路径: {baidu_batch}")
    try:
        client = BaiduPCSClient()
        if not client.load_login():
            print("  ❌ BaiduPCS 登录失败")
        else:
            baidu_summary = cleanup_baidu_batch_folder(client, baidu_batch, junk_files)
            if baidu_summary["total_deleted"] > 0:
                print(f"\n  📊 Baidu 清理汇总: 删 {baidu_summary['total_deleted']} 个文件, 涉及 {len(baidu_summary['folders_with_junk'])} 个文件夹")
    except Exception as e:
        print(f"  ❌ Baidu 清理出错: {e}")

    print(f"\n✅ 清理完成\n")


if __name__ == "__main__":
    asyncio.run(main())
