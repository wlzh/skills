"""Quark batch runner v2.0.0: save-share lockstep with title tracking.

Each item is saved AND shared in one step, capturing the title→URL mapping
explicitly (no longer order-dependent on get_sorted_file_list).

Title rules:
- If items.json has both title + url → use the provided title
- If items.json has only url (empty/no title) → use the actual Quark folder name
- If one title has two URLs → both saved under the same title (merged later)

Usage:
  cd /Users/m./Documents/QNSZ/project/QuarkPanTool
  . .venv/bin/activate
  python /Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/scripts/quark_batch_run.py \
    --label "短裤哥批次" \
    --month 202603 \
    --items-json /path/to/items.json \
    --out-json /path/to/batch_share_results.json

items.json format:
  [
    {"title": "xxx", "url": "https://pan.quark.cn/s/...."},
    ...
  ]

Notes:
- Requires Quark cookies to exist at QuarkPanTool/config/cookies.txt (run quark_login.py if needed).
"""

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

# 自动加载 secrets.env（如果存在）
SECRETS_ENV = Path(__file__).resolve().parent.parent.parent.parent / "QuarkPanTool" / "config" / "secrets.env"
if SECRETS_ENV.exists():
    for line in SECRETS_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip())

from quark import QuarkPanFileManager
from utils import read_config

from share_folder_items import get_share_id_with_retry


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--label", default="短裤哥批次")
    p.add_argument("--month", default="")
    p.add_argument("--items-json", required=True)
    p.add_argument("--out-json", required=True)
    p.add_argument("--headless", action="store_true", default=True)
    return p.parse_args()


async def list_all_items(mgr, pdir_fid):
    """Get ALL items in a directory, handling pagination."""
    all_items = []
    page = 1
    size = 200
    while True:
        data = await mgr.get_sorted_file_list(pdir_fid=pdir_fid, page=str(page), size=str(size), fetch_total='true')
        lst = (data.get('data') or {}).get('list') or []
        meta = data.get('metadata') or {}
        all_items.extend(lst)
        total = meta.get('_total') or 0
        _size = meta.get('_size') or size
        _page = meta.get('_page') or page
        if _size * _page >= total:
            break
        page += 1
    return all_items


async def main():
    args = parse_args()

    items = json.loads(Path(args.items_json).read_text(encoding="utf-8"))
    norm_items = []
    for it in items:
        title = (it.get("title") or "").strip()
        url = (it.get("url") or it.get("input_url") or "").strip()
        if not url:
            continue
        norm_items.append((title, url))

    mgr = QuarkPanFileManager(headless=True, slow_mo=0)

    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    batch_folder_name = f"{ts}_{args.label}"
    await mgr.create_dir(batch_folder_name)

    cfg = read_config('./config/config.json', read_type='json')
    to_dir_id = cfg['pdir_id']

    share_results = []

    for idx, (title, url) in enumerate(norm_items, 1):
        print(f"\n==== ({idx}/{len(norm_items)}) {title or '(无标题，将使用实际文件夹名)'} ====")
        print(f"  source: {url}")

        # 1. Pre-save snapshot: record existing file FIDs
        before = {item['fid'] for item in await list_all_items(mgr, to_dir_id)}

        # 2. Save the source URL to batch folder
        await mgr.run(url, folder_id=to_dir_id, download=False)

        # 3. Post-save snapshot: find newly created files/folders
        after = await list_all_items(mgr, to_dir_id)
        new_items = [item for item in after if item['fid'] not in before]

        if not new_items:
            print(f"  ⚠️ 未检测到新保存的文件（可能已存在），跳过")
            continue

        for item in new_items:
            fid = item['fid']
            quark_name = item['file_name']

            # User rule:
            # - 有 title + url → 用提供的 title
            # - 只有 url（title为空）→ 用 Quark 实际文件夹名
            effective_title = title if title else quark_name

            # 4. Create encrypted share link for this saved item
            print(f"  sharing: {quark_name} ...", end=" ")
            task_id = await mgr.get_share_task_id(fid, quark_name, url_type=2, expired_type=1, password='')
            share_id = await get_share_id_with_retry(mgr, task_id, timeout_sec=90)
            share_url, _ = await mgr.submit_share(share_id)

            share_results.append({
                "title": effective_title,
                "quark_name": quark_name,
                "fid": fid,
                "share_id": share_id,
                "share_url": share_url,
            })
            print(f"-> {share_url}")

    out = {
        "batch_folder_name": batch_folder_name,
        "batch_folder_fid": to_dir_id,
        "items": [{"title": t, "input_url": u} for t, u in norm_items],
        "share_results": share_results,
    }

    Path(args.out_json).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[DONE] wrote {args.out_json}")
    print(f"Batch folder: {batch_folder_name}\n")


if __name__ == '__main__':
    asyncio.run(main())
