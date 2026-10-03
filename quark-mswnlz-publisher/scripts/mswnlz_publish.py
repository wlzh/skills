"""Publish Quark batch share results into local mswnlz content dirs + deploy site to Cloudflare Pages.

Inputs:
- batch_share_results.json produced by quark_batch_run.py
- target month YYYYMM

Behavior:
- Classify items into content dirs (book/movies default; extensible).
- Append to YYYYMM.md and update README.md month index.
- Commit locally (content dirs are git repos; GitHub 远端已随账号封禁废弃，仅保留本地版本历史).
- Rebuild site and deploy to Cloudflare Pages (deploy_cloudflare_pages.sh).
- Send unified notification to Telegram groups (one message for all dirs).

Token handling:
- Telegram token 只从环境变量读取（TELEGRAM_BOT_TOKEN），不硬编码。
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
        PROJECT_ROOT / "mswnlz",
        PROJECT_ROOT / "mswnlz-github",
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
    # GitHub 远端已废弃（账号封禁），内容仓库只认本地目录
    repo_dir = MSWNLZ_ROOT / repo
    if repo_dir.exists():
        return
    raise FileNotFoundError(
        f"本地内容目录不存在: {repo_dir}（GitHub 克隆已废弃，请在 MSWNLZ_ROOT 下准备好该目录）"
    )


def fetch_mswnlz_repo_descriptions() -> Dict[str, str]:
    # 仓库描述改为本地配置（原 GitHub API 已随账号封禁不可用）
    desc_file = Path(__file__).parent / "config" / "repo_descriptions.json"
    return json.loads(desc_file.read_text(encoding="utf-8"))


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


# 标准资源行格式：[标题](URL)
_LINK_LINE_RE = re.compile(r'^\[(.+?)\]\((https?://\S+?)\)\s*$')


def normalize_legacy_lines(text: str) -> tuple[str, int]:
    """把旧格式行统一转成 [标题](URL)，清除标题水印，并确保相邻链接行之间有空行。

    处理变体:
      A: -? 标题-超过100T资料总站网站-doc.869hr.uk | URL
      C: [标题-超过100T资料总站网站xxx](URL)  → 清除水印后缀
      D: 带 -/数字| 前缀、或 |提取码 后缀的链接行，同样清水印
    """
    converted = 0
    intermediate = []
    # 水印后缀三种形态：-超过100T资料总站网站-doc.869hr.uk / 超过100T资料总站网站doc.869hr.uk / -doc.869hr.uk
    watermark_re = re.compile(r'\s*-?(?:超过100T资料总站网站-?)?doc\.869hr\.uk\s*$')

    for line in text.splitlines():
        # 变体A: 旧管道格式 标题-水印 | URL
        m = re.match(
            r'^-?\s*(.+?)-超过100T资料总站网站-?doc\.869hr\.uk\s*\|\s*(https?://\S+)',
            line,
        )
        if m:
            title, url = m.group(1).strip(), m.group(2).strip()
            safe = title.replace("[", "【").replace("]", "】")
            intermediate.append(f"[{safe}]({url})")
            converted += 1
            continue

        # 变体C/D: [标题-水印](URL)。先剥离 -/数字| 前缀和 |提取码 后缀，再清水印。
        stripped = line.strip()
        prefix_m = re.match(r'^(?:[-*]\s+|\d+[|、.]\s*)(.*)$', stripped)
        if prefix_m:
            stripped = prefix_m.group(1).strip()
        suffix_m = re.match(r'^(.*?)\s*\|\s*提取码[：:].*$', stripped)
        if suffix_m:
            stripped = suffix_m.group(1).strip()

        m = _LINK_LINE_RE.match(stripped)
        if m and watermark_re.search(m.group(1)):
            title = watermark_re.sub('', m.group(1)).strip()
            title = re.sub(r'[-—–\s]+$', '', title).strip()
            url = m.group(2)
            safe = title.replace("[", "【").replace("]", "】")
            intermediate.append(f"[{safe}]({url})")
            converted += 1
            continue

        intermediate.append(line)

    # 第二遍：在相邻的 [标题](URL) 行之间插入空行
    # VitePress 会把相邻文本行合并为一个段落，导致渲染成一坨
    final_lines = []
    prev_was_link = False
    blanks_added = 0
    for line in intermediate:
        is_link = bool(_LINK_LINE_RE.match(line))
        if is_link and prev_was_link:
            final_lines.append("")  # 插入空行
            blanks_added += 1
        final_lines.append(line)
        prev_was_link = is_link

    result = "\n".join(final_lines) + ("\n" if text.endswith("\n") else "")
    return result, converted + blanks_added


def append_items(month_file: Path, items: List[Tuple[str, str]]):
    month_file.parent.mkdir(parents=True, exist_ok=True)
    existing = month_file.read_text(encoding="utf-8") if month_file.exists() else ""

    # 自动修复旧格式 + 清水印 + 补空行
    if '超过100T资料总站网站' in existing or _needs_blank_separation(existing):
        existing, n = normalize_legacy_lines(existing)
        if n:
            print(f"[FIX] {month_file.name}: 自动规范化 {n} 行")

    out = existing.rstrip("\n") + ("\n" if existing.strip() else "")
    existing_urls = set(re.findall(r"https?://[^\s<>)|]+", existing))
    for title, url in items:
        if url in existing_urls:
            print(f"[SKIP] existing URL in {month_file.name}: {title}")
            continue
        safe_title = title.replace("[", "【").replace("]", "】").strip()
        # 新增条目前确保和上文有空行隔开
        if out and not out.endswith("\n\n"):
            out += "\n"
        out += f"[{safe_title}]({url})\n"
        existing_urls.add(url)
    month_file.write_text(out, encoding="utf-8")


def _needs_blank_separation(text: str) -> bool:
    """检测是否存在相邻的 [标题](URL) 行之间缺空行的情况。"""
    lines = text.splitlines()
    prev_was_link = False
    for line in lines:
        is_link = bool(_LINK_LINE_RE.match(line))
        if is_link and prev_was_link:
            return True
        prev_was_link = is_link
    return False


def migrate_legacy_all(dry_run: bool = False) -> Tuple[int, List[str]]:
    """全量规范化所有内容仓库的所有 YYYYMM.md。

    背景：normalize_legacy_lines 只在 append_items 里跑（仅当前批次月份），
    历史月份文件里的旧水印/管道格式（`标题-超过100T资料总站网站… | URL`）永远不会被
    触碰，导致站点 catalog 里长期残留水印标题。本函数一次性扫描全部内容仓库迁移到位。
    """
    if not MSWNLZ_ROOT.exists():
        print(f"[MIGRATE] 内容根目录不存在: {MSWNLZ_ROOT}")
        return 0, []

    skip = {"mswnlz.github.io", "mswnlz", "docs", ".git"}
    content_repos = sorted(
        p for p in MSWNLZ_ROOT.iterdir()
        if p.is_dir() and (p / ".git").exists() and p.name not in skip
    )

    total_converted = 0
    touched = []
    for repo_dir in content_repos:
        for month_file in sorted(repo_dir.glob("*.md")):
            if not re.fullmatch(r"\d{6}\.md", month_file.name):
                continue
            text = month_file.read_text(encoding="utf-8")
            if '超过100T资料总站网站' not in text and 'doc.869hr.uk' not in text and not _needs_blank_separation(text):
                continue
            new_text, n = normalize_legacy_lines(text)
            if not n:
                continue
            rel = f"{repo_dir.name}/{month_file.name}"
            if dry_run:
                print(f"[MIGRATE-dry] {rel}: 将规范化 {n} 行")
            else:
                month_file.write_text(new_text, encoding="utf-8")
                print(f"[MIGRATE] {rel}: 规范化 {n} 行")
            total_converted += n
            touched.append(rel)

    return total_converted, touched


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
    ap.add_argument("--month", help="目标月份 YYYYMM（发布模式必填）")
    ap.add_argument("--batch-json", help="batch_share_results.json 路径（发布模式必填）")
    ap.add_argument("--dry-run", action="store_true", help="模拟运行：跳过TG通知、本地提交与站点部署")
    ap.add_argument("--migrate-legacy", action="store_true", help="全量迁移所有内容仓库的旧水印/管道格式")
    args = ap.parse_args()

    # ── 迁移模式：独立于发布流程，一次性规范化全部历史月份文件 ──
    if args.migrate_legacy:
        total, touched = migrate_legacy_all(dry_run=args.dry_run)
        print(f"\n[MIGRATE] 共规范化 {total} 行，涉及 {len(touched)} 个文件")
        if args.dry_run:
            print("   （dry-run，未写盘。去掉 --dry-run 执行实际迁移）")
            return
        if touched:
            repos = sorted({f.split("/", 1)[0] for f in touched})
            print(f"\n[MIGRATE] 提交 {len(repos)} 个内容仓库...")
            for repo in repos:
                repo_dir = MSWNLZ_ROOT / repo
                try:
                    sh(["git", "add", "-A", "*.md"], cwd=repo_dir)
                    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(repo_dir)).returncode == 0:
                        print(f"[SKIP] no changes for {repo}")
                        continue
                    sh(["git", "commit", "-m", "chore: 规范化旧水印格式为标准链接 [标题](URL)"], cwd=repo_dir)
                    print(f"[OK] committed {repo}")
                except Exception as e:
                    print(f"[WARN] {repo} 本地提交失败: {e}")
        return

    if not args.month or not args.batch_json:
        ap.error("发布模式需要 --month 和 --batch-json（或用 --migrate-legacy 进入迁移模式）")

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
        # 兼容两种格式: quark_batch_run (name/quark_name/share_url) 和 pipeline_orchestrator (name/links)
        name = it.get("name") or it.get("quark_name") or it.get("title") or ""
        links = it.get("links", {})
        share_url = it.get("share_url") or ""
        if not name:
            continue
        # 如果没有 links 字段但有 share_url，构造单链接 links
        if not links and share_url:
            links = {"quark": share_url}
        
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
        print("[dry-run] 跳过本地提交与站点部署")
    else:
        for repo, items in by_repo_github.items():
            ensure_clone(repo)
            repo_dir = MSWNLZ_ROOT / repo
            sh(["git", "checkout", "main"], cwd=repo_dir)

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

            updated_repos.append(repo)
            total_items += len(items)
            print(f"[OK] committed {repo}: {len(items)} items")

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
    """本地构建并部署站点到 Cloudflare Pages（原 GitHub Actions 已废弃）"""
    script_dir = Path(__file__).parent
    trigger_script = script_dir / "trigger_site_rebuild.sh"

    if trigger_script.exists():
        import subprocess
        try:
            # 构建 + 部署全流程（含 VitePress 全量构建与 wrangler 上传），需要较长时间
            result = subprocess.run(
                ["bash", str(trigger_script)],
                cwd=str(script_dir),
                capture_output=True,
                text=True,
                timeout=1800
            )
            if result.returncode == 0:
                print(f"[OK] 站点已构建并部署到 Cloudflare Pages")
                # 只打印关键尾部日志，避免刷屏
                tail = "\n".join(result.stdout.splitlines()[-12:])
                print(tail)
            else:
                print(f"[WARN] 站点部署失败: {result.stderr[-500:]}")
        except Exception as e:
            print(f"[WARN] 站点部署异常: {e}")
    else:
        print(f"[WARN] trigger_site_rebuild.sh 不存在，跳过站点部署")


if __name__ == "__main__":
    main()
