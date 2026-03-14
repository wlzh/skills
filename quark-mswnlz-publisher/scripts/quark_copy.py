"""Copy promotional files from template folder to shared folders.

This module copies files from a predefined template folder (temp/要共享的文件)
to each newly created shared folder in Quark Drive.
"""

import asyncio
import random
from pathlib import Path
from typing import List, Optional

import httpx

from utils import get_timestamp, custom_print


class QuarkFileCopier:
    """Copy files between folders in Quark Drive."""

    # 推广文件模板文件夹路径（夸克网盘中的路径）
    PROMO_FOLDER_PATH = "temp/要共享的文件"

    def __init__(self, cookies: str, headers: dict):
        self.cookies = cookies
        self.headers = headers.copy()

    async def get_folder_fid_by_path(self, path: str) -> Optional[str]:
        """根据路径获取文件夹的 FID"""
        api = "https://drive-pc.quark.cn/1/clouddrive/file/sort"
        params = {
            'pr': 'ucpro',
            'fr': 'pc',
            'uc_param_str': '',
            'pdir_fid': '0',
            '_page': '1',
            '_size': '50',
            '_sort': 'file_type:asc,updated_at:desc',
            '__t': get_timestamp(13),
        }

        # 按路径逐级查找
        parts = path.strip('/').split('/')
        current_fid = '0'

        async with httpx.AsyncClient() as client:
            for part in parts:
                params['pdir_fid'] = current_fid
                response = await client.get(api, headers=self.headers, params=params)
                data = response.json()

                if data.get('status') != 200:
                    return None

                found = False
                for item in data.get('data', {}).get('list', []):
                    if item.get('file_name') == part and item.get('file_type') == 'folder':
                        current_fid = item.get('fid')
                        found = True
                        break

                if not found:
                    custom_print(f"[WARN] 未找到文件夹: {part}")
                    return None

        return current_fid

    async def list_folder_files(self, folder_fid: str) -> List[dict]:
        """列出文件夹中的所有文件"""
        api = "https://drive-pc.quark.cn/1/clouddrive/file/sort"
        params = {
            'pr': 'ucpro',
            'fr': 'pc',
            'uc_param_str': '',
            'pdir_fid': folder_fid,
            '_page': '1',
            '_size': '100',
            '_sort': 'file_type:asc,updated_at:desc',
            '__t': get_timestamp(13),
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(api, headers=self.headers, params=params)
            data = response.json()

            if data.get('status') != 200:
                return []

            return data.get('data', {}).get('list', [])

    async def copy_files(self, file_fids: List[str], to_folder_fid: str) -> bool:
        """复制文件到目标文件夹"""
        api = "https://drive-pc.quark.cn/1/clouddrive/file/copy"
        params = {
            'pr': 'ucpro',
            'fr': 'pc',
            'uc_param_str': '',
            '__dt': random.randint(100, 9999),
            '__t': get_timestamp(13),
        }
        data = {
            "action": "copy",
            "exclude_fids": [],
            "filelist": file_fids,
            "to_pdir_fid": to_folder_fid,
        }

        async with httpx.AsyncClient() as client:
            timeout = httpx.Timeout(60.0, connect=60.0)
            response = await client.post(api, json=data, headers=self.headers, params=params, timeout=timeout)
            result = response.json()

            if result.get('status') == 200:
                task_id = result.get('data', {}).get('task_id')
                custom_print(f"[OK] 复制任务已创建: {task_id}")
                return True
            else:
                custom_print(f"[ERROR] 复制失败: {result.get('message')}")
                return False

    async def copy_promo_files_to_folder(self, target_folder_fid: str) -> List[str]:
        """复制推广文件到目标文件夹"""
        # 1. 获取推广文件模板文件夹的 FID
        promo_folder_fid = await self.get_folder_fid_by_path(self.PROMO_FOLDER_PATH)
        if not promo_folder_fid:
            custom_print(f"[ERROR] 未找到推广文件模板文件夹: {self.PROMO_FOLDER_PATH}")
            custom_print(f"[INFO] 请确保已在夸克网盘中创建该文件夹并上传推广文件")
            return []

        # 2. 列出推广文件
        promo_files = await self.list_folder_files(promo_folder_fid)
        if not promo_files:
            custom_print(f"[WARN] 推广文件模板文件夹为空")
            return []

        # 3. 复制文件
        file_fids = [f['fid'] for f in promo_files]
        file_names = [f['file_name'] for f in promo_files]

        custom_print(f"[INFO] 复制 {len(file_fids)} 个推广文件...")

        success = await self.copy_files(file_fids, target_folder_fid)

        if success:
            custom_print(f"[OK] 已复制推广文件: {', '.join(file_names)}")
            return file_names
        else:
            return []


async def add_promo_files_to_folder(cookies: str, headers: dict, folder_fid: str):
    """Add promotional files to a Quark Drive folder."""
    copier = QuarkFileCopier(cookies, headers)
    return await copier.copy_promo_files_to_folder(folder_fid)
