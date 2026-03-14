"""Publish Quark batch share results into mswnlz GitHub content repos.

Inputs:
- batch_share_results.json produced by quark_batch_run.py
- target month YYYYMM

Behavior:
- Classify items into repos (book/movies default; extensible).
- Append to YYYYMM.md and update README.md month index.
- Commit + push via SSH.

Token handling:
- GitHub API calls do not require auth for small usage; if rate-limited, set GITHUB_TOKEN env var.
"""

import argparse
import json
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import urllib.request

PROJECT_ROOT = Path("/Users/m./Documents/QNSZ/project")
MSWNLZ_ROOT = PROJECT_ROOT / "mswnlz"

SITE_SUFFIX = "-超过100T资料总站网站-doc.869hr.uk"


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    ap.add_argument("--batch-json", required=True)
    args = ap.parse_args()

    batch = json.loads(Path(args.batch_json).read_text(encoding="utf-8"))
    share_results = batch.get("share_results") or []

    repo_desc = fetch_mswnlz_repo_descriptions()

    by_repo: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    for it in share_results:
        name = it.get("name") or ""
        url = it.get("share_url") or ""
        if not name or not url:
            continue
        repo = classify_item(name, repo_desc)
        by_repo[repo].append((name, url))

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

        print(f"[OK] pushed {repo}: {len(items)} items")


if __name__ == "__main__":
    main()
