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
from typing import Dict, List, Optional, Tuple

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

def first_existing_path(paths: List[Optional[Path]], fallback: Path) -> Path:
    for candidate in paths:
        if candidate and candidate.exists():
            return candidate
    return fallback


PROJECT_ROOT = first_existing_path(
    [
        Path(os.environ["QNSZ_PROJECT_ROOT"]) if os.environ.get("QNSZ_PROJECT_ROOT") else None,
        Path("/Users/m/document/QNSZ/project"),
    ],
    Path("/Users/m/document/QNSZ/project"),
)
MSWNLZ_ROOT = first_existing_path(
    [
        Path(os.environ["MSWNLZ_CONTENT_ROOT"]) if os.environ.get("MSWNLZ_CONTENT_ROOT") else None,
        PROJECT_ROOT / "mswnlz-github",
        PROJECT_ROOT / "mswnlz",
    ],
    PROJECT_ROOT / "mswnlz-github",
)

# Telegram 配置 - 从环境变量读取，不要硬编码！
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_GROUPS = [
    {"chat_id": os.environ.get("TG_GROUP_1_ID", ""), "thread_id": os.environ.get("TG_GROUP_1_THREAD", "5")},
    {"chat_id": os.environ.get("TG_GROUP_2_ID", ""), "thread_id": os.environ.get("TG_GROUP_2_THREAD", "2")},
    {"chat_id": os.environ.get("TG_GROUP_3_ID", ""), "thread_id": None},
    {"chat_id": os.environ.get("TG_GROUP_4_ID", ""), "thread_id": os.environ.get("TG_GROUP_4_THREAD", "")},
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
    token = os.environ.get("GITHUB_TOKEN")
    # Use curl with retry to avoid IncompleteRead errors
    cmd = ["curl", "-s", "--retry", "3", "--retry-delay", "2", "-H", "Accept: application/vnd.github+json"]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd += [url]
    import subprocess as _sp
    r = _sp.run(cmd, capture_output=True, text=True, timeout=30)
    data = json.loads(r.stdout)
    return {repo["name"]: (repo.get("description") or "") for repo in data}


def classify_item(name: str, repo_desc: Dict[str, str], original_title: str = "") -> str:
    """
    根据资源名称和原始标题自动归类到 mswnlz 仓库。
    
    分层策略：
      第一关 — 视频/影视类关键词命中 → movies
      第二关 — 书籍类关键词命中       → book
      第三关 — 按仓库 description 评分  → 兜底
    
    说明：
      - 原始标题（用户输入的完整名称）辅助判断，弥补 Quark 文件夹名简写的问题
      - 视频关键词优先（4K、超清、蓝光等分辨率词几乎只用于视频）
      - "合集"不再直接归 book，防止影视合集误归
    """
    n = name + " " + original_title

    # ── 第一关：视频/影视类关键词 ──
    # 分辨率标识（几乎只用于视频）
    if re.search(r"\b4K\b|超清|蓝光|高清|1080P|2160P|720P", n, re.IGNORECASE):
        return "movies"
    # 影视关键短语
    if re.search(r"电影|纪录片|纪录[片影视]|演唱会|电视剧|剧集|连续剧|TV版|影视", n):
        return "movies"
    # 集数标识（第X集 / 全X集 / X集全）
    if re.search(r"全\d+集|第\d+集|第.{0,3}集|\d+集全|\d+集完结", n):
        return "movies"
    # 常见视频后缀
    if re.search(r"\.mp4|\.mkv|\.avi|\.rmvb|\.mov|\.ts|\.webm", n, re.IGNORECASE):
        return "movies"

    # ── 第二关：书籍类关键词 ──
    # 注意：谨慎使用"合集"（"BBC纪录片合集"不该归书），此处只匹配明确书籍词
    if re.search(r"书$|书单|新书|电子书|杂志|纯文本|\d+册|\d+本|册全书|全集书", n):
        return "book"

    # ── 第三关（回退）：按仓库描述评分 ──
    # 当名称和标题都无法明确判断时，用仓库 description 关键词做模糊匹配

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
    existing_urls = set(re.findall(r"https?://[^\s<>)|]+", existing))
    for title, url in items:
        if url in existing_urls:
            print(f"[SKIP] existing URL in {month_file.name}: {title}")
            continue
        safe_title = title.replace("[", "【").replace("]", "】").strip()
        out += f"[{safe_title}]({url})\n"
        existing_urls.add(url)
    month_file.write_text(out, encoding="utf-8")


def make_commit_message(items: List[str]) -> str:
    # One item per line, no URLs
    lines = [f"增加 {t}" for t in items]
    return "\n".join(lines)


def send_telegram_group_notification(updated_repos: List[str], total_items: int, by_repo: Dict[str, List[Tuple[str, str]]], month: str, source: str = "quark"):
    """发送统一的群组通知（只发一条）"""
    import urllib.parse
    
    if not updated_repos:
        return
    
    # 根据来源使用不同文案
    link_label = "夸克链接" if source == "quark" else ("百度链接" if source == "baidu" else "")
    
    # 构建资源列表
    item_lines = []
    for repo in updated_repos:
        items = by_repo.get(repo, [])
        for name, url in items:
            if source == "combined":
                # 双链接：url 已包含夸克/百度标签
                item_lines.append(f"增加 {name}\n{url}")
            else:
                item_lines.append(f"增加 {name}\n🔗 {link_label}：{url}")
    
    repos_str = "、".join(updated_repos)
    items_text = "\n\n".join(item_lines)
    
    text = f"📦 新增资源推送\n\n{items_text}\n\n已更新仓库：{repos_str}\n\n🔗 查看详情：https://doc.869hr.uk/{updated_repos[0]}/{month}\n🌐 资料总站：https://doc.869hr.uk\n📦 资料频道：https://t.me/dabaziyuan"
    
    for group in TELEGRAM_GROUPS:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": group["chat_id"],
            "text": text
        }
        if group.get("thread_id"):
            data["message_thread_id"] = group["thread_id"]
        
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


def generate_quark_group_message(by_repo: Dict[str, List[Tuple[str, str]]], batch_folder: str, source: str = "quark") -> str:
    """生成网盘群组消息（格式化，方便复制）"""
    source_label = "夸克" if source == "quark" else ("百度" if source == "baidu" else ("阿里云盘" if source == "aliyun" else ""))
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
            url_lines = url.split("\n")
            for ul in url_lines:
                lines.append(f"  🔗 {ul}" if not ul.startswith("🔗") else f"  {ul}")
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
    ap.add_argument("--dry-run", action="store_true", help="模拟运行：跳过TG通知和GitHub推送")
    args = ap.parse_args()

    batch = json.loads(Path(args.batch_json).read_text(encoding="utf-8"))
    share_results = batch.get("share_results") or []
    batch_folder = batch.get("batch_folder_name", "")

    repo_desc = fetch_mswnlz_repo_descriptions()

    # 构建原始标题映射（按顺序匹配 Quark 文件名与原始标题）
    items_meta = batch.get("items") or []
    original_titles = {}
    for im in items_meta:
        orig = (im.get("title") or "").strip()
        if orig:
            original_titles[orig] = orig

    # 构建通知用的（带双链接文本）和 GitHub 用的（单 URL）
    by_repo_notify: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    by_repo_github: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    
    for idx, it in enumerate(share_results):
        name = it.get("name") or ""
        links = it.get("links", {})
        share_url = it.get("share_url") or ""
        if not name:
            continue
        
        # 获取原始标题
        orig_title = ""
        if idx < len(items_meta):
            orig_title = items_meta[idx].get("title") or ""
        repo = classify_item(name, repo_desc, original_title=orig_title)
        
        # 通知用：支持多链接显示
        if len(links) > 1:
            parts = []
            if links.get("quark"):
                parts.append(f"夸克：{links['quark']}")
            if links.get("baidu"):
                parts.append(f"百度：{links['baidu']}")
            if links.get("aliyun"):
                parts.append(f"阿里云盘：{links['aliyun']}")
            url_display = "\n".join(parts)
        else:
            url_display = share_url or next(iter(links.values()), "")
        
        if url_display:
            by_repo_notify[repo].append((name, url_display))
        
        # GitHub 用：优先取夸克链接，其次阿里云盘，再百度
        gh_url = links.get("quark") or links.get("aliyun", "") or links.get("baidu", "")
        if gh_url:
            by_repo_github[repo].append((name, gh_url))

    updated_repos = []
    total_items = 0
    
    if args.dry_run:
        print("[dry-run] 跳过 GitHub 推送")
    else:
        for repo, items in by_repo_github.items():
            ensure_clone(repo)
            repo_dir = MSWNLZ_ROOT / repo
            git_pull(repo_dir)

            month_file = repo_dir / f"{args.month}.md"
            append_items(month_file, items)

            readme_path = repo_dir / "README.md"
            readme = readme_path.read_text(encoding="utf-8")
            readme_path.write_text(readme_insert_month(readme, args.month), encoding="utf-8")

            sh(["git", "add", f"{args.month}.md", "README.md"], cwd=repo_dir)
            if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(repo_dir)).returncode == 0:
                print(f"[SKIP] no changes for {repo}")
                continue
            msg = make_commit_message([t for t, _ in items])
            sh(["git", "commit", "-m", msg], cwd=repo_dir)
            sh(["git", "push", "origin", "main"], cwd=repo_dir)

            updated_repos.append(repo)
            total_items += len(items)
            print(f"[OK] pushed {repo}: {len(items)} items")

    # 获取来源
    source = batch.get("source", "quark")
    
    # 生成群组消息并保存
    group_msg = generate_quark_group_message(by_repo_notify, batch_folder, source=source)
    msg_filename = f"{source}_group_message.txt"
    msg_file = Path(args.batch_json).parent / msg_filename
    msg_file.write_text(group_msg, encoding="utf-8")
    print(f"\n[{source.upper()}群组消息] 已保存到: {msg_file}")
    print("-" * 40)
    print(group_msg)
    print("-" * 40)

    # 统一发送群组通知（dry-run 跳过）
    if updated_repos and not args.dry_run:
        print(f"\n[TG] 发送群组汇总通知...")
        send_telegram_group_notification(updated_repos, total_items, by_repo_notify, args.month, source=source)
    elif args.dry_run:
        print(f"\n[dry-run] 跳过 TG 通知")

    # 触发网站更新（dry-run 跳过）
    if updated_repos and not args.dry_run:
        print(f"\n[网站] 触发站点重建...")
        trigger_site_rebuild()
    elif args.dry_run:
        print(f"[dry-run] 跳过站点重建")

    print("")
    if args.dry_run:
        print(f"[dry-run] 模拟完成，共 {total_items} 项")
        print(f"   手动发布命令：")
        print(f"     python3 {__file__} --month {args.month} --batch-json {args.batch_json}")


def trigger_site_rebuild():
    """触发 mswnlz.github.io 站点重建"""
    script_dir = Path(__file__).parent
    trigger_script = script_dir / "trigger_site_rebuild.sh"
    
    if trigger_script.exists():
        import subprocess
        try:
            result = subprocess.run(
                ["bash", str(trigger_script)],
                cwd=str(script_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f"[OK] 网站更新已触发")
                print(result.stdout)
            else:
                print(f"[WARN] 网站更新触发失败: {result.stderr}")
        except Exception as e:
            print(f"[WARN] 网站更新触发异常: {e}")
    else:
        print(f"[WARN] trigger_site_rebuild.sh 不存在，跳过网站更新")


if __name__ == "__main__":
    main()
