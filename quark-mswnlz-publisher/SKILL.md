---
name: quark-mswnlz-publisher
description: "Automate the full QuarkPanTool → mswnlz GitHub content publishing pipeline. Use when the user provides Quark share URLs and wants: (1) create a batch folder in Quark Drive, (2) save/copy resources into that folder, (3) generate permanent encrypted share links with random passcodes, (4) auto-classify items into mswnlz repos (book/movies/etc.) by repo descriptions, (5) append/update the target repo's YYYYMM.md and README month index, (6) git commit+push, and (7) force-trigger mswnlz.github.io site rebuild and return the final site URLs."
---

# quark-mswnlz-publisher

## Workspace conventions

- Default working root: `/Users/m./Documents/QNSZ/project`
- Quark automation repo: `/Users/m./Documents/QNSZ/project/QuarkPanTool`
- mswnlz org repos local root: `/Users/m./Documents/QNSZ/project/mswnlz`
- Skills repo (wlzh): `/Users/m./Documents/QNSZ/project/skills`

## Safety / secrets

- Never echo or paste user tokens back into chat.
- Prefer GitHub SSH remotes (`git@github.com:...`) to avoid storing tokens in git config.
- If a token is required for GitHub API calls, accept it as an env var at runtime (do not write to files).

## End-to-end workflow

### 0) Inputs to collect/confirm

- A list of Quark share URLs (each item may include a title).
- Target month `YYYYMM` (default: current month in Asia/Shanghai).
- Batch folder name format: `YYYY-MM-DD_HHMM_<label>` (default label: `短裤哥批次`).

### 1) Ensure Quark cookies exist (login only if needed)

- Check `QuarkPanTool/config/cookies.txt`.
- If missing/empty: run `python quark_login.py` (uses Chrome channel) and wait for user to finish login.

### 2) Run batch: save URLs to Quark + generate encrypted permanent share links

- Use the provided script pattern (see `scripts/quark_batch_run.py`) to:
  1. Create a new folder in Quark root.
  2. Save all input share URLs into that folder.
  3. List the folder items.
  4. For each top-level item, create a share link with:
     - `url_type=2` (encrypted)
     - `expired_type=1` (permanent)
     - random passcode if not given
  5. Produce a JSON output: `batch_share_results.json` with:
     - batch folder name + fid
     - original input items
     - share results: name, fid, share_url

### 3) Auto-classify each share result into mswnlz repos

- Fetch `https://api.github.com/users/mswnlz/repos?per_page=100&sort=updated` and build mapping:
  - repo_name → description
- Classification heuristic:
  - If item name contains影视/剧/电影/纪录片/演唱会 → `movies`
  - If item name contains书/书单/新书/杂志/电子书/合集 → `book`
  - Otherwise, fall back to best match by repo description keywords (book/movies/curriculum/tools/etc.).
- Persist the mapping to `references/mswnlz-repos-cache.json` (safe: public info only).

### 4) Update target content repos

For each target repo (e.g., `book`, `movies`):

- Ensure local clone exists in `/Users/m./Documents/QNSZ/project/mswnlz/<repo>` (clone via SSH if missing).
- Ensure on `main`, `git pull --rebase`.
- Append to `<YYYYMM>.md`:
  - One item per line:
    `- {title}-超过100T资料总站网站-doc.869hr.uk | {share_url}`
- Update `README.md` month index line:
  - Keep months in reverse chronological order.
  - Add the new `YYYYMM` link if missing.
- Commit message rules:
  - Remove URLs from commit message.
  - One item per line, prefix with `增加 `.
- Push to `origin main`.

### 5) Trigger site rebuild (mswnlz.github.io)

Because local `gh` CLI may be missing, use **push-trigger**:

- In `/Users/m./Documents/QNSZ/project/mswnlz/mswnlz.github.io`:
  - `git pull --rebase`
  - `git commit --allow-empty -m "chore: trigger site rebuild"`
  - `git push origin main`
- Optionally poll latest Actions run:
  - `https://api.github.com/repos/mswnlz/mswnlz.github.io/actions/runs?per_page=1`
- Final site base URL (from CNAME): `https://doc.869hr.uk`

### 6) Final output to user

Return:
- Batch folder name
- All share URLs (with passcodes already in URL)
- For each item: chosen repo + appended file (`YYYYMM.md`)
- Actions run URL (if available)
- Site URL list (at minimum: category pages)

## Bundled scripts

- `scripts/quark_batch_run.py`: Quark save+share JSON builder.
- `scripts/mswnlz_publish.py`: Apply classification, update repos, commit+push.
- `scripts/trigger_site_rebuild.sh`: allow-empty commit push trigger.
