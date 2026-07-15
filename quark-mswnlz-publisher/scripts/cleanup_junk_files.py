"""
cleanup_junk_files.py — 清理网盘资源文件夹内的垃圾文件

在全流程中的位置：A段 save → 🧹 这里 → share → promo_copy → 发布

工作方式：
  读取 batch_share_results.json → 连接对应网盘 → 遍历批次文件夹下每个子文件夹
  → 列出子文件夹内所有文件 → 匹配垃圾文件名单（子串匹配）→ 删除

用法：
  python3 cleanup_junk_files.py --batch-json batch_share_results.json \\
      --junk-config config/junk_files.json

参数：
  --junk-config: 垃圾文件名单配置（支持子串匹配）
  --quark-parent-fid: 夸克批次文件夹的父目录 FID（默认 0=根目录）
  --baidu-batch-path: 百度批次文件夹路径（如 /短裤哥批次）
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


async def cleanup_quark_batch_folder(mgr: QuarkPanFileManager, batch_folder_fid: str, junk_files: list) -> dict:
    """扫描 Quark 批次文件夹下全部子文件夹，清理所有匹配的垃圾文件"""
    summary = {"total_deleted": 0, "total_folders": 0, "folders_with_junk": [], "details": []}

    # 获取所有子文件夹
    children = await get_quark_folder_children(mgr, batch_folder_fid)
    subdirs = [c for c in children if c.get("dir")]

    print(f"  📁 共 {len(subdirs)} 个子文件夹")

    for sd in subdirs:
        sub_name = sd.get("file_name", "?")
        sub_fid = sd["fid"]

        # 列出子文件夹内文件
        files = await get_quark_folder_children(mgr, sub_fid)
        target_files = [f for f in files if not f.get("dir") and match_junk(f.get("file_name", ""), junk_files)]

        if target_files:
            fids_to_delete = [f["fid"] for f in target_files]
            names_deleted = [f.get("file_name", "?") for f in target_files]
            await mgr.delete_files(fids_to_delete, pdir_fid=sub_fid)
            summary["total_deleted"] += len(fids_to_delete)
            summary["folders_with_junk"].append(sub_name)
            summary["details"].append({
                "folder": sub_name,
                "deleted": names_deleted,
                "count": len(names_deleted)
            })
            print(f"    🗑️ [{sub_name}] 删 {len(names_deleted)} 个: {', '.join(names_deleted)}")
        else:
            print(f"    ✅ [{sub_name}] 无垃圾文件")

    summary["total_folders"] = len(subdirs)
    return summary


def cleanup_baidu_batch_folder(client: BaiduPCSClient, batch_path: str, junk_files: list) -> dict:
    """扫描 Baidu 批次文件夹下全部子文件夹，清理所有匹配的垃圾文件

    BaiduPCS-Go 的 ls 输出中，目录 size='-'，文件 size 为数字。
    如果某项目是目录，递归进入子目录扫描；如果是文件（电影等），在根部扫描。
    """
    summary = {"total_deleted": 0, "total_folders": 0, "folders_with_junk": [], "details": []}

    entries = client.ls(batch_path)
    # BaiduPCS-Go: size='-' 表示目录，否则是文件
    dirs = [e for e in entries if e.get("size", "").strip() == "-"]
    files = [e for e in entries if e.get("size", "").strip() not in ("", "-")]

    print(f"  📁 共 {len(dirs)} 个子文件夹, {len(files)} 个文件")

    # 扫描各个子文件夹内的文件
    for sd in dirs:
        sub_name = sd.get("name", "?")
        sub_path = f"{batch_path}/{sub_name}"

        sub_entries = client.ls(sub_path)
        # 子文件夹内可能还有子文件夹（如2026年07月/0701/），只需扫描文件
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
                "folder": sub_name,
                "deleted": deleted_names,
                "count": len(deleted_names)
            })
            print(f"    🗑️ [{sub_name}] 删 {len(deleted_names)} 个: {', '.join(deleted_names)}")
        else:
            print(f"    ✅ [{sub_name}] 无垃圾文件")

    summary["total_folders"] = len(dirs)
    return summary


async def main():
    p = argparse.ArgumentParser(description="清理网盘资源文件夹内垃圾文件")
    p.add_argument("--batch-json", required=True, help="batch_share_results.json 路径")
    p.add_argument("--junk-config", required=True, help="junk_files.json 路径")
    p.add_argument("--quark-parent-fid", default="0", help="夸克批次文件夹的父目录 FID")
    p.add_argument("--baidu-batch-path", default="/短裤哥批次", help="百度批次文件夹路径")
    args = p.parse_args()

    batch = json.loads(Path(args.batch_json).read_text(encoding="utf-8"))
    junk_files = load_junk_config(args.junk_config)

    print(f"\n🧹 垃圾文件清理 ({len(junk_files)} 个模式)")
    print(f"   模式: {', '.join(junk_files)}\n")

    # ── Quark 清理 ───────────────────────────────────────
    batch_folder_name = batch.get("batch_folder_name", "")
    if batch_folder_name:
        print(f"\n☁️  Quark 清理 — 批次文件夹: {batch_folder_name}")
        try:
            mgr = QuarkPanFileManager(headless=True, slow_mo=0)
            # 批次文件夹一定在根目录下，直接搜根目录
            parent_fid = "0"
            batch_fid = await get_quark_batch_folder_fid(mgr, parent_fid, batch_folder_name)
            if not batch_fid:
                print(f"  ❌ 在根目录找不到夸克批次文件夹: {batch_folder_name}")
                # 尝试列出根目录前 10 个文件夹
                data = await mgr.get_sorted_file_list(pdir_fid=parent_fid, page="1", size="20", fetch_total="true")
                names = [i.get("file_name","") for i in (data.get("data") or {}).get("list") or [] if i.get("dir")]
                print(f"  根目录最近文件夹: {names[:5]}")
            else:
                print(f"  ✅ 找到批次文件夹 FID: {batch_fid}")
                quark_summary = await cleanup_quark_batch_folder(mgr, batch_fid, junk_files)
                if quark_summary["total_deleted"] > 0:
                    print(f"\n  📊 Quark 清理汇总: 删 {quark_summary['total_deleted']} 个文件, 涉及 {len(quark_summary['folders_with_junk'])} 个文件夹")
        except Exception as e:
            print(f"  ❌ Quark 清理出错: {e}")

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
