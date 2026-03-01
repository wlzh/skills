#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeSpy skill wrapper.

- Ensures upstream WeSpy source exists at ~/Documents/QNSN/project/WeSpy
- Clones upstream repository automatically if missing
- Delegates CLI behavior to upstream wespy.main.main
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

UPSTREAM_REPO = "https://github.com/tianchangNorth/WeSpy.git"
BASE_DIR = Path.home() / "Documents" / "QNSN" / "project"
WESPY_DIR = BASE_DIR / "WeSpy"


def ensure_wespy_repo() -> Path:
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    if not WESPY_DIR.exists():
        print(f"[wespy-fetcher] 未检测到 WeSpy，正在克隆到: {WESPY_DIR}")
        subprocess.run(["git", "clone", UPSTREAM_REPO, str(WESPY_DIR)], check=True)

    if not (WESPY_DIR / "wespy" / "main.py").exists():
        raise RuntimeError(f"无效的 WeSpy 目录: {WESPY_DIR}")

    return WESPY_DIR


def main() -> int:
    repo_dir = ensure_wespy_repo()
    sys.path.insert(0, str(repo_dir))

    try:
        from wespy.main import main as wespy_main  # type: ignore
    except Exception as exc:
        print(f"[wespy-fetcher] 导入 wespy.main 失败: {exc}", file=sys.stderr)
        print("请检查依赖是否已安装：pip3 install -r scripts/requirements.txt", file=sys.stderr)
        return 1

    wespy_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
