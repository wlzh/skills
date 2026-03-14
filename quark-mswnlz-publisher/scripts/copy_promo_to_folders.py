"""Copy promotional files to each shared resource folder.

Usage:
  cd /Users/m./Documents/QNSZ/project/QuarkPanTool
  . .venv/bin/activate
  python /Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/scripts/copy_promo_to_folders.py \
    --batch-json batch_share_results.json

This script:
1. Reads batch_share_results.json to get share_results (each item's fid)
2. For each item in share_results, checks if it's a folder
3. If it's a folder, copies promo files INTO that folder

Promo files location: temp/要共享的文件 (FID: 87b3b2740c284ada8e513d59ce81aa96)
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "QuarkPanTool"))

import httpx


class QuarkPromoCopier:
    """Copy promotional files to each shared folder."""

    PROMO_FOLDER_FID = "87b3b2740c284ada8e513d59ce81aa96"  # temp/要共享的文件

    def __init__(self, cookies: str, headers: dict = None):
        self.cookies = cookies
        self.headers = headers or {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'origin': 'https://pan.quark.cn',
            'referer': 'https://pan.quark.cn/',
            'cookie': cookies,
        }

    async def list_folder_files(self, client: httpx.AsyncClient, folder_fid: str) -> tuple:
        """列出文件夹中的所有项目
        
        Returns:
            tuple: (is_folder: bool, items: list or None)
        """
        api = "https://drive-pc.quark.cn/1/clouddrive/file/sort"
        params = {
            'pr': 'ucpro',
            'fr': 'pc',
            'pdir_fid': folder_fid,
            '_page': '1',
            '_size': '100',
        }

        resp = await client.get(api, headers=self.headers, params=params)
        data = resp.json()

        if data.get('status') != 200:
            return (False, None)
        
        # 如果返回了 data 字段，说明是文件夹
        if 'data' in data:
            return (True, data.get('data', {}).get('list', []))
        
        return (False, None)

    async def copy_files(self, client: httpx.AsyncClient, file_fids: List[str], to_folder_fid: str) -> bool:
        """复制文件到目标文件夹"""
        api = "https://drive-pc.quark.cn/1/clouddrive/file/copy"
        params = {
            'pr': 'ucpro',
            'fr': 'pc',
        }
        data = {
            "filelist": file_fids,
            "to_pdir_fid": to_folder_fid,
        }

        resp = await client.post(api, headers=self.headers, params=params, json=data)
        result = resp.json()

        return result.get('status') == 200

    async def copy_promo_to_all_folders(self, share_results: List[dict]) -> dict:
        """复制推广文件到每个分享文件夹内部"""
        results = {"success": [], "skipped": [], "failed": []}

        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. 获取推广文件列表
            is_folder, promo_items = await self.list_folder_files(client, self.PROMO_FOLDER_FID)
            if not is_folder or not promo_items:
                print("[ERROR] 推广文件模板文件夹为空或无法访问")
                print(f"[INFO] 请确保夸克网盘中存在 'temp/要共享的文件' 文件夹")
                return results

            promo_fids = [f['fid'] for f in promo_items]
            print(f"[INFO] 找到 {len(promo_fids)} 个推广文件")

            # 2. 遍历每个分享结果
            for item in share_results:
                name = item.get('name', '')
                fid = item.get('fid', '')

                if not fid:
                    results["skipped"].append(name)
                    continue

                # 检查这个 fid 是否是文件夹
                is_folder, folder_items = await self.list_folder_files(client, fid)

                if is_folder:
                    # 是文件夹，复制推广文件进去
                    print(f"\n[处理] {name}")
                    success = await self.copy_files(client, promo_fids, fid)

                    if success:
                        print(f"  ✅ 推广文件已复制到文件夹内部")
                        results["success"].append(name)
                    else:
                        print(f"  ❌ 复制失败")
                        results["failed"].append(name)
                else:
                    # 是文件，跳过
                    print(f"\n[跳过] {name} (不是文件夹)")
                    results["skipped"].append(name)

        return results
                    results["skipped"].append(name)

        return results


async def copy_promo_files(batch_json_path: str, cookies: str, headers: dict = None) -> dict:
    """Main function to copy promo files to all shared folders.
    
    Args:
        batch_json_path: Path to batch_share_results.json
        cookies: Quark cookies string
        headers: Optional headers dict
        
    Returns:
        dict with success, skipped, failed lists
    """
    # 读取批次结果
    batch = json.loads(Path(batch_json_path).read_text(encoding="utf-8"))
    share_results = batch.get("share_results", [])

    if not share_results:
        print("[WARN] 没有找到分享结果")
        return {"success": [], "skipped": [], "failed": []}

    print(f"[INFO] 共 {len(share_results)} 个资源需要处理")

    # 执行复制
    copier = QuarkPromoCopier(cookies, headers)
    return await copier.copy_promo_to_all_folders(share_results)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-json", required=True)
    args = ap.parse_args()

    # 读取 cookies
    cookies_path = Path(__file__).parent.parent.parent.parent / "QuarkPanTool" / "config" / "cookies.txt"
    if not cookies_path.exists():
        print(f"[ERROR] Cookies 文件不存在: {cookies_path}")
        return
    
    cookies = cookies_path.read_text().strip()

    # 执行复制
    results = await copy_promo_files(args.batch_json, cookies)

    print(f"\n[完成]")
    print(f"  ✅ 成功: {len(results['success'])}")
    print(f"  ⏭️ 跳过: {len(results['skipped'])}")
    print(f"  ❌ 失败: {len(results['failed'])}")


if __name__ == "__main__":
    asyncio.run(main())
