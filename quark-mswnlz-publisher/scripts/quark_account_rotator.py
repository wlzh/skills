#!/usr/bin/env python3
"""
quark_account_rotator.py — 夸克多账号轮换器（方案B：按批次轮换，做法甲：cookie 文件复制）

功能：
  - 维护多个夸克账号的 cookie 文件（cookies_1.txt, cookies_2.txt, ...）
  - 每次调用自动轮换到下一个账号
  - 将当前账号的 cookie 复制为 cookies.txt（QuarkPanTool 的 quark.py 零改动）
  - 记录轮换历史到 account_state.json

使用方式（被 pipeline_orchestrator.py 或 quark_batch_run.py 调用）：
  from quark_account_rotator import rotate_to_next_account, get_current_account

  # 获取当前应该使用的账号
  account_id = rotate_to_next_account(config_dir)

  # 或仅查询（不轮换）
  account_id = get_current_account(config_dir)

状态文件：{config_dir}/account_state.json
Cookie 文件：{config_dir}/cookies_{N}.txt

Version: 1.0.0
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def _state_path(config_dir: str | Path) -> Path:
    return Path(config_dir) / "account_state.json"


def _cookie_path(config_dir: str | Path, account_id: int) -> Path:
    return Path(config_dir) / f"cookies_{account_id}.txt"


def _active_cookie_path(config_dir: str | Path) -> Path:
    return Path(config_dir) / "cookies.txt"


def load_state(config_dir: str | Path) -> dict:
    """读取轮换状态"""
    sp = _state_path(config_dir)
    if sp.exists():
        return json.loads(sp.read_text(encoding="utf-8"))
    # 初始化
    state = {
        "current_account": 1,
        "total_accounts": 2,
        "last_rotation_at": "",
        "history": []
    }
    sp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state


def save_state(config_dir: str | Path, state: dict) -> None:
    """保存轮换状态"""
    sp = _state_path(config_dir)
    sp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def discover_accounts(config_dir: str | Path) -> List[int]:
    """扫描 config_dir 下所有 cookies_N.txt，返回账号 ID 列表（升序）"""
    ids = []
    for p in Path(config_dir).glob("cookies_*.txt"):
        stem = p.stem  # cookies_1
        if stem.startswith("cookies_"):
            try:
                aid = int(stem.split("_", 1)[1])
                ids.append(aid)
            except ValueError:
                continue
    return sorted(ids)


def get_available_accounts(config_dir: str | Path) -> List[int]:
    """获取可用的账号列表（cookie 文件存在且非空）"""
    ids = discover_accounts(config_dir)
    valid = []
    for aid in ids:
        p = _cookie_path(config_dir, aid)
        if p.exists() and p.stat().st_size > 10:
            valid.append(aid)
    return valid


def activate_account(config_dir: str | Path, account_id: int) -> bool:
    """
    将指定账号的 cookie 复制为 cookies.txt（做法甲：零侵入）

    Returns:
        True 如果成功，False 如果 cookie 文件不存在
    """
    src = _cookie_path(config_dir, account_id)
    dst = _active_cookie_path(config_dir)

    if not src.exists():
        print(f"[ROTATOR] ❌ cookies_{account_id}.txt 不存在")
        return False

    # 备份当前 cookies.txt（如果有）
    backup = Path(config_dir) / "cookies.txt.bak"
    if dst.exists():
        shutil.copy2(dst, backup)

    shutil.copy2(src, dst)
    print(f"[ROTATOR] ✅ 已激活账号 {account_id}（cookies_{account_id}.txt → cookies.txt）")
    return True


def rotate_to_next_account(config_dir: str | Path, force_account: Optional[int] = None) -> int:
    """
    轮换到下一个账号并激活

    Args:
        config_dir: QuarkPanTool/config 目录路径
        force_account: 强制使用指定账号（跳过自动轮换），用于某账号被限速时的临时指定

    Returns:
        当前激活的账号 ID
    """
    state = load_state(config_dir)
    available = get_available_accounts(config_dir)

    if not available:
        print("[ROTATOR] ⚠️ 没有找到任何可用的账号 cookie 文件，保持当前 cookies.txt 不变")
        return state.get("current_account", 1)

    if force_account is not None:
        if force_account not in available:
            print(f"[ROTATOR] ❌ 指定账号 {force_account} 不可用（cookie 文件不存在或为空）")
            # 回退到自动轮换
        else:
            current = force_account
            activate_account(config_dir, current)
            state["current_account"] = current
            state["total_accounts"] = len(available)
            state["last_rotation_at"] = datetime.now().isoformat()
            state["history"].append({
                "timestamp": datetime.now().isoformat(),
                "action": "force",
                "account": current,
            })
            # 只保留最近 50 条历史
            state["history"] = state["history"][-50:]
            save_state(config_dir, state)
            return current

    # 自动轮换：找到当前账号在可用列表中的位置，取下一个
    current = state.get("current_account", 1)
    if current not in available:
        # 当前账号不在可用列表中，从第一个开始
        next_account = available[0]
    else:
        idx = available.index(current)
        next_idx = (idx + 1) % len(available)
        next_account = available[next_idx]

    activate_account(config_dir, next_account)

    state["current_account"] = next_account
    state["total_accounts"] = len(available)
    state["last_rotation_at"] = datetime.now().isoformat()
    state["history"].append({
        "timestamp": datetime.now().isoformat(),
        "action": "rotate",
        "from": current,
        "to": next_account,
    })
    # 只保留最近 50 条历史
    state["history"] = state["history"][-50:]
    save_state(config_dir, state)

    return next_account


def get_current_account(config_dir: str | Path) -> int:
    """获取当前记录的账号 ID（不轮换、不复制）"""
    state = load_state(config_dir)
    return state.get("current_account", 1)


def get_account_info(config_dir: str | Path, account_id: int) -> dict:
    """获取账号信息"""
    cookie_path = _cookie_path(config_dir, account_id)
    return {
        "account_id": account_id,
        "cookie_file": str(cookie_path),
        "exists": cookie_path.exists(),
        "size": cookie_path.stat().st_size if cookie_path.exists() else 0,
    }


def status(config_dir: str | Path) -> dict:
    """获取完整状态信息"""
    state = load_state(config_dir)
    available = get_available_accounts(config_dir)
    accounts_info = [get_account_info(config_dir, aid) for aid in available]

    return {
        "current_account": state.get("current_account", 1),
        "total_accounts": state.get("total_accounts", len(available)),
        "available_accounts": available,
        "last_rotation_at": state.get("last_rotation_at", ""),
        "history": state.get("history", [])[-10:],
        "accounts_detail": accounts_info,
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="夸克多账号轮换器")
    ap.add_argument("--config-dir", default="./config", help="QuarkPanTool/config 目录")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("status", help="查看当前状态")
    sub.add_parser("next", help="轮换到下一个账号")
    sub.add_parser("list", help="列出所有可用账号")

    ap_force = sub.add_parser("force", help="强制指定账号")
    ap_force.add_argument("account_id", type=int, help="账号 ID")

    args = ap.parse_args()

    if args.cmd == "status":
        info = status(args.config_dir)
        print(json.dumps(info, ensure_ascii=False, indent=2))
    elif args.cmd == "next":
        aid = rotate_to_next_account(args.config_dir)
        print(f"✅ 轮换完成，当前账号: {aid}")
    elif args.cmd == "list":
        available = get_available_accounts(args.config_dir)
        print(f"可用账号: {available}")
        for aid in available:
            info = get_account_info(args.config_dir, aid)
            print(f"  账号{aid}: {info['cookie_file']} ({info['size']} bytes)")
    elif args.cmd == "force":
        aid = rotate_to_next_account(args.config_dir, force_account=args.account_id)
        print(f"✅ 强制切换到账号: {aid}")
    else:
        ap.print_help()
