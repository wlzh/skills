"""Publish Quark batch share results into mswnlz GitHub content repos.

Inputs:
- batch_share_results.json produced by quark_batch_run.py
- target month YYYYMM

Behavior:
- Classify items into repos (book/movies default; extensible).
- Append to YYYYMM.md and update README.md month index.
- Commit + push via SSH.
- Send unified notification to Telegram groups (one message for all repos).

Token handling:
- GitHub API calls do not require auth for small usage; if rate-limited, set GITHUB_TOKEN env var.
"""

import argparse
import json
import os
import re
import subprocess
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path("/Users/m./Documents/QNSZ/project")
MSWNLZ_ROOT = PROJECT_ROOT / "mswnlz"

SITE_SUFFIX = "-超过100T资料总站网站-doc.869hr.uk"

# Telegram 配置 - 从环境变量读取，不要硬编码！
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_GROUPS = [
    {"chat_id": os.environ.get("TG_GROUP_1_ID", ""), "thread_id": os.environ.get("TG_GROUP_1_THREAD", "5")},
    {"chat_id": os.environ.get("TG_GROUP_2_ID", ""), "thread_id": os.environ.get("TG_GROUP_2_THREAD", "2")},
]

# 频道 ID
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@dabaziyuan")


def sh(cmd: List[str], cwd: Path) -> str:
    p = subprocess.run(cmd, cwd=str(cwd), check=True, capture_output=True, text=True)
    return p.stdout.strip()


def ensure_clone(repo: str):
    repo_dir = MSWNLZ_ROOT / repo
    if repo_dir.exists():
        return
    sh(["git", "clone", "--depth", "1", f"git@github.com:mswnlz/{repo}.git"], cwd=MSWNLZ_ROOT)


def git_pull(repo_dir: Path):
    sh(["git", "checkout", "main"], cwd=repo_dir)
    sh(["git", "pull", "--rebase"], cwd=repo_dir)


def fetch_mswnlz_repo_descriptions() -> Dict[str, str]:
    url = "https://api.github.com/users/mswnlz/repos?per_page=100&sort=updated"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return {r["name"]: (r.get("description") or "") for r in data}


def classify_item(name: str, repo_desc: Dict[str, str]) -> str:
    n = name
    if re.search(r"影视|电影|剧|纪录片|演唱会", n):
        return "movies"
    if re.search(r"书|书单|新书|杂志|电子书|合集", n):
        return "book"

    # fallback keyword match against descriptions
    candidates = [
        "book",
        "movies",
        "curriculum",
        "tools",
        "healthy",
        "self-media",
        "cross-border",
        "edu-knowlege",
        "AIknowledge",
    ]
    best = "curriculum"
    best_score = -1
    for c in candidates:
        desc = repo_desc.get(c, "")
        score = 0
        for kw in ["书", "影视", "课程", "工具", "健康", "自媒体", "跨境", "教育", "AI"]:
            if kw in desc and kw in n:
                score += 2
            if kw in n:
                score += 1
        if score > best_score:
            best_score = score
            best = c
    return best


def readme_insert_month(readme: str, month: str) -> str:
    # Expect a line like: # [202603](202603.md) [202510](...) ...
    lines = readme.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("# [") and "](202" in line:
            if f"[{month}]({month}.md)" in line:
                return readme
            # insert month right after '# '
            parts = line.split(" ")
            # parts[0] == '#'
            new_line = parts[0] + " " + f"[{month}]({month}.md)" + " " + " ".join(parts[1:])
            lines[i] = new_line
            return "\n".join(lines) + "\n"

    # fallback: prepend a header index block
    header = f"# [{month}]({month}.md)\n\n"
    return header + readme


def append_items(month_file: Path, items: List[Tuple[str, str]]):
    month_file.parent.mkdir(parents=True, exist_ok=True)
    existing = month_file.read_text(encoding="utf-8") if month_file.exists() else ""
    out = existing.rstrip("\n") + ("\n" if existing.strip() else "")
    for title, url in items:
        out += f"- {title}{SITE_SUFFIX} | {url}\n"
    month_file.write_text(out, encoding="utf-8")


def make_commit_message(items: List[str]) -> str:
    # One item per line, no URLs
    lines = [f"增加 {t}" for t in items]
    return "\n".join(lines)


def send_telegram_group_notification(updated_repos: List[str], total_items: int):
    """发送统一的群组通知（只发一条）"""
    import urllib.parse
    
    if not updated_repos:
        return
    
    repos_str = "、".join(updated_repos)
    text = f"📝 资源更新\n\n已更新仓库：{repos_str}\n共 {total_items} 项资源\n\n📦 https://t.me/dabaziyuan"
    
    for group in TELEGRAM_GROUPS:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": group["chat_id"],
            "message_thread_id": group["thread_id"],
            "text": text
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=urllib.parse.urlencode(data).encode("utf-8"),
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if result.get("ok"):
                    print(f"[TG] 发送到群组 {group['chat_id']} 话题 {group['thread_id']} ✅")
                else:
                    print(f"[TG] 发送失败: {result.get('description')}")
        except Exception as e:
            print(f"[TG] 发送异常: {e}")


def generate_quark_group_message(by_repo: Dict[str, List[Tuple[str, str]]], batch_folder: str) -> str:
    """生成夸克群组消息（格式化，方便复制）"""
    lines = ["📦 资源更新通知", ""]
    
    total = 0
    for repo, items in by_repo.items():
        repo_names = {
            "book": "📚 书籍资料",
            "movies": "🎬 影视资源",
            "AIknowledge": "🤖 AI知识",
            "curriculum": "🎓 课程教程",
            "edu-knowlege": "📖 教育知识",
            "healthy": "💪 健康养生",
            "self-media": "📱 自媒体",
            "cross-border": "🌍 跨境电商",
            "chinese-traditional": "🏮 传统文化",
            "tools": "🔧 工具软件",
        }
        lines.append(f"\n{repo_names.get(repo, '📁')} {repo}")
        lines.append("-" * 30)
        
        for name, url in items:
            lines.append(f"• {name}")
            lines.append(f"  🔗 {url}")
            total += 1
    
    lines.append("")
    lines.append("=" * 40)
    lines.append(f"🌐 资料总站：https://doc.869hr.uk")
    lines.append(f"📂 批次文件夹：{batch_folder}")
    lines.append(f"📊 共 {total} 项资源")
    
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    ap.add_argument("--batch-json", required=True)
    args = ap.parse_args()

    batch = json.loads(Path(args.batch_json).read_text(encoding="utf-8"))
    share_results = batch.get("share_results") or []
    batch_folder = batch.get("batch_folder_name", "")

    repo_desc = fetch_mswnlz_repo_descriptions()

    by_repo: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    for it in share_results:
        name = it.get("name") or ""
        url = it.get("share_url") or ""
        if not name or not url:
            continue
        repo = classify_item(name, repo_desc)
        by_repo[repo].append((name, url))

    updated_repos = []
    total_items = 0
    
    for repo, items in by_repo.items():
        ensure_clone(repo)
        repo_dir = MSWNLZ_ROOT / repo
        git_pull(repo_dir)

        month_file = repo_dir / f"{args.month}.md"
        append_items(month_file, items)

        readme_path = repo_dir / "README.md"
        readme = readme_path.read_text(encoding="utf-8")
        readme_path.write_text(readme_insert_month(readme, args.month), encoding="utf-8")

        sh(["git", "add", f"{args.month}.md", "README.md"], cwd=repo_dir)
        msg = make_commit_message([t for t, _ in items])
        sh(["git", "commit", "-m", msg], cwd=repo_dir)
        sh(["git", "push", "origin", "main"], cwd=repo_dir)

        updated_repos.append(repo)
        total_items += len(items)
        print(f"[OK] pushed {repo}: {len(items)} items")

    # 生成夸克群组消息并保存
    quark_msg = generate_quark_group_message(by_repo, batch_folder)
    quark_msg_file = Path(args.batch_json).parent / "quark_group_message.txt"
    quark_msg_file.write_text(quark_msg, encoding="utf-8")
    print(f"\n[夸克群组消息] 已保存到: {quark_msg_file}")
    print("-" * 40)
    print(quark_msg)
    print("-" * 40)

    # 统一发送群组通知（只发一条）
    if updated_repos:
        print(f"\n[TG] 发送群组汇总通知...")
        send_telegram_group_notification(updated_repos, total_items)


if __name__ == "__main__":
    main()
