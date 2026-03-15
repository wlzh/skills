"""Quark batch runner: create folder → save a list of share URLs → generate encrypted permanent share links.

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
SECRETS_ENV = Path(__file__).parent.parent.parent / "QuarkPanTool/config/secrets.env"
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


async def main():
    args = parse_args()

    items = json.loads(Path(args.items_json).read_text(encoding="utf-8"))
    norm_items = []
    for it in items:
        title = (it.get("title") or "").strip() or "未命名"
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

    for idx, (title, url) in enumerate(norm_items, 1):
        print(f"\n==== ({idx}/{len(norm_items)}) 转存：{title} ====")
        await mgr.run(url, folder_id=to_dir_id, download=False)

    share_results = []
    page = 1
    size = 100
    while True:
        data = await mgr.get_sorted_file_list(pdir_fid=to_dir_id, page=str(page), size=str(size), fetch_total='true')
        lst = (data.get('data') or {}).get('list') or []
        meta = data.get('metadata') or {}

        for item in lst:
            fid = item.get('fid')
            name = item.get('file_name')
            if not fid or not name:
                continue

            # url_type=2 encrypted, expired_type=1 permanent, password='' => random
            task_id = await mgr.get_share_task_id(fid, name, url_type=2, expired_type=1, password='')
            share_id = await get_share_id_with_retry(mgr, task_id, timeout_sec=90)
            share_url, _ = await mgr.submit_share(share_id)
            share_results.append({"name": name, "fid": fid, "share_id": share_id, "share_url": share_url})
            print(f"[SHARE] {name} -> {share_url}")

        total = meta.get('_total') or 0
        _size = meta.get('_size') or size
        _page = meta.get('_page') or page
        if _size * _page >= total:
            break
        page += 1

    out = {
        "batch_folder_name": batch_folder_name,
        "batch_folder_fid": to_dir_id,
        "items": [{"title": t, "input_url": u} for t, u in norm_items],
        "share_results": share_results,
    }

    Path(args.out_json).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[DONE] wrote {args.out_json}\n")


if __name__ == '__main__':
    asyncio.run(main())
