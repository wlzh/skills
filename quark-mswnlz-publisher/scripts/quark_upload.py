"""Upload promotional files to Quark Drive folders.

This module adds promotional files (readme, password hints, etc.) to folders
after batch copying shared items to Quark Drive.
"""

import asyncio
import hashlib
import os
from pathlib import Path
from typing import List, Optional

import httpx

from utils import get_timestamp


class QuarkUploader:
    """Upload files to Quark Drive using the upload API."""

    PROMO_FILES_DIR = Path("/Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/promo_files")

    def __init__(self, cookies: str, headers: dict):
        self.cookies = cookies
        self.headers = headers.copy()
        self.headers.update({
            'content-type': 'application/json',
        })

    async def get_upload_url(self, file_name: str, file_size: int, pdir_fid: str) -> dict:
        """Get pre-upload info from Quark API."""
        url = "https://drive-pc.quark.cn/1/clouddrive/file/pupload"
        params = {
            'pr': 'ucpro',
            'fr': 'pc',
            'uc_param_str': '',
            '__t': get_timestamp(13),
        }
        data = {
            "file_name": file_name,
            "file_size": file_size,
            "pdir_fid": pdir_fid,
            "mode": 1,  # normal upload
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, params=params, headers=self.headers)
            return response.json()

    async def upload_file(self, file_path: Path, pdir_fid: str) -> Optional[str]:
        """Upload a single file to Quark Drive folder."""
        if not file_path.exists():
            print(f"[WARN] 文件不存在: {file_path}")
            return None

        file_size = file_path.stat().st_size
        file_name = file_path.name

        # 1. 获取上传 URL
        preupload = await self.get_upload_url(file_name, file_size, pdir_fid)
        if preupload.get('status') != 200:
            print(f"[ERROR] 获取上传 URL 失败: {preupload.get('message')}")
            return None

        upload_url = preupload['data'].get('upload_url')
        task_id = preupload['data'].get('task_id')

        if not upload_url:
            print(f"[ERROR] 未获取到上传 URL")
            return None

        # 2. 上传文件内容
        async with httpx.AsyncClient() as client:
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f, 'application/octet-stream')}
                headers = self.headers.copy()
                headers.pop('content-type', None)  # 让 httpx 自动设置 multipart

                response = await client.put(
                    upload_url,
                    content=f.read(),
                    headers={'Content-Type': 'application/octet-stream'},
                    timeout=httpx.Timeout(300.0)
                )

                if response.status_code not in [200, 201]:
                    print(f"[ERROR] 上传失败: HTTP {response.status_code}")
                    return None

        # 3. 提交上传完成
        commit_url = "https://drive-pc.quark.cn/1/clouddrive/file/upload/commit"
        params = {
            'pr': 'ucpro',
            'fr': 'pc',
            'uc_param_str': '',
            '__t': get_timestamp(13),
        }
        data = {
            "task_ids": [task_id],
            "pdir_fid": pdir_fid,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(commit_url, json=data, params=params, headers=self.headers)
            result = response.json()

            if result.get('status') == 200:
                print(f"[OK] 上传成功: {file_name}")
                return task_id
            else:
                print(f"[ERROR] 提交失败: {result.get('message')}")
                return None

    async def upload_promo_files(self, pdir_fid: str) -> List[str]:
        """Upload all promotional files to a folder."""
        uploaded = []

        if not self.PROMO_FILES_DIR.exists():
            print(f"[WARN] 推广文件目录不存在: {self.PROMO_FILES_DIR}")
            return uploaded

        promo_files = list(self.PROMO_FILES_DIR.glob('*'))
        print(f"[INFO] 找到 {len(promo_files)} 个推广文件")

        for file_path in promo_files:
            if file_path.is_file():
                task_id = await self.upload_file(file_path, pdir_fid)
                if task_id:
                    uploaded.append(file_path.name)

        return uploaded


async def add_promo_files_to_folder(cookies: str, headers: dict, folder_fid: str):
    """Add promotional files to a Quark Drive folder."""
    uploader = QuarkUploader(cookies, headers)
    return await uploader.upload_promo_files(folder_fid)
