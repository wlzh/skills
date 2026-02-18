---
name: x-fetcher
description: 抓取 X (Twitter) 推文和长文章的命令行工具。支持普通推文（文字、图片、视频链接）和 X Article 长文章（完整正文，Markdown 格式），自动保存为 Markdown 文件。基于 Jane-xiaoer/x-fetcher 项目。Use when user mentions "抓取推文", "下载推文", "保存 X 文章", "fetch tweet", or provides x.com/twitter.com URLs.
---

# X Fetcher

抓取 X (Twitter) 帖子内容的命令行工具，支持普通推文和 X Article 长文章，自动保存为 Markdown 格式。

**工程化来源**: 本 Skill 基于 [Jane-xiaoer/x-fetcher](https://github.com/Jane-xiaoer/x-fetcher) 项目。

## 功能

- 抓取普通推文（文字、图片、视频链接）
- 抓取 X Article 长文章（完整正文，Markdown 格式）
- 获取互动数据（点赞、转发、浏览量、书签数）
- 自动保存为格式化的 Markdown 文件
- 可配置默认下载目录

## Script Directory

脚本位于 `scripts/` 子目录。

**路径解析**:
1. `SKILL_DIR` = 此 SKILL.md 文件所在目录
2. 脚本路径 = `${SKILL_DIR}/scripts/main.py`

## Preferences (EXTEND.md)

使用 Bash 检查 EXTEND.md 是否存在（优先级顺序）:

```bash
# 首先检查项目级
test -f .x-fetcher/EXTEND.md && echo "project"

# 然后检查用户级（跨平台：$HOME 适用于 macOS/Linux/WSL）
test -f "$HOME/.x-fetcher/EXTEND.md" && echo "user"
```

┌────────────────────────────────────┬───────────────────┐
│                路径                │     位置          │
├────────────────────────────────────┼───────────────────┤
│ .x-fetcher/EXTEND.md               │ 项目目录          │
├────────────────────────────────────┼───────────────────┤
│ $HOME/.x-fetcher/EXTEND.md         │ 用户主目录        │
└────────────────────────────────────┴───────────────────┘

┌───────────┬───────────────────────────────────────────────────────────────────────────┐
│  结果     │                                  动作                                     │
├───────────┼───────────────────────────────────────────────────────────────────────────┤
│ 已找到    │ 读取、解析、应用设置                                                       │
├───────────┼───────────────────────────────────────────────────────────────────────────┤
│ 未找到    │ **必须**运行首次设置（见下文）— **不要**静默创建默认值                       │
└───────────┴───────────────────────────────────────────────────────────────────────────┘

**EXTEND.md 支持**: 默认下载目录 | 媒体处理方式

### 首次设置（阻塞式）

**关键**: 当未找到 EXTEND.md 时，在创建 EXTEND.md 之前，你**必须使用 `AskUserQuestion`** 询问用户的偏好。**绝不**要在未询问的情况下创建带有默认值的 EXTEND.md。这是一个**阻塞式**操作 — 在设置完成之前**不要**继续进行任何转换。

在**一次**调用中使用 `AskUserQuestion` 提出所有问题：

**问题 1** — header: "下载目录", question: "推文保存的默认目录路径？"
- "x-fetcher（推荐）" — 保存到 ./x-fetcher/{username}/{tweet-id}.md
- （用户可以选择 "Other" 来输入自定义路径）

**问题 2** — header: "保存位置", question: "偏好设置保存到？"
- "用户（推荐）" — ~/.x-fetcher/（所有项目）
- "项目" — .x-fetcher/（仅此项目）

用户回答后，在所选位置创建 EXTEND.md，确认 "偏好设置已保存到 [path]"，然后继续。

### 支持的配置键

| 键 | 默认值 | 可选值 | 描述 |
|-----|---------|--------|-------------|
| `default_output_dir` | 空 | 路径或空 | 默认输出目录（空 = `./x-fetcher/`） |
| `auto_save` | `true` | `true` / `false` | 自动保存 Markdown 文件 |
| `download_media` | `ask` | `ask` / `true` / `false` | 是否下载媒体文件到本地（`ask` = 每次询问，`true` = 总是下载，`false` = 从不下载） |

**值优先级**:
1. CLI 参数
2. EXTEND.md
3. Skill 默认值

**媒体下载说明**:
- 当 `download_media` 设置为 `true` 时，图片会保存到 `imgs/` 目录，视频保存到 `videos/` 目录
- Markdown 文件中的媒体链接会自动更新为本地相对路径
- 支持的媒体格式：图片（jpg, png, gif, webp），视频（mp4, mov, webm）

## 使用

```bash
python3 ${SKILL_DIR}/scripts/main.py <url>
python3 ${SKILL_DIR}/scripts/main.py <url> --output /path/to/save
python3 ${SKILL_DIR}/scripts/main.py <url> --download-media
python3 ${SKILL_DIR}/scripts/main.py <url> --json
```

## 选项

| 选项 | 描述 |
|--------|-------------|
| `<url>` | 推文或文章 URL |
| `--output <path>` | 输出路径（目录或文件） |
| `--download-media` | 下载图片/视频资源到本地 `imgs/` 和 `videos/`，并将 Markdown 链接重写为本地相对路径 |
| `--json` | JSON 输出（不保存 Markdown） |
| `--no-save` | 不自动保存 Markdown 文件 |

## 支持的 URL

- `https://x.com/<user>/status/<id>`
- `https://twitter.com/<user>/status/<id>`

## 输出

### 普通推文

```markdown
# @username 的推文

> 作者: **Author Name** (@username)
> 发布时间: 2024-01-01 12:00:00
> 原文链接: https://x.com/user/status/123

---

推文内容...

## 媒体

![媒体1](https://pbs.twimg.com/media/example.jpg)

---

## 互动数据

- ❤️ 点赞: 1,234
- 🔁 转发: 567
- 👀 浏览: 89,000
- 💬 回复: 123
```

### X Article 长文章

```markdown
# 文章标题

> 作者: **Author Name** (@username)
> 发布时间: 2024-01-01 12:00:00
> 修改时间: 2024-01-02 10:30:00
> 原文链接: https://x.com/user/status/123

---

![封面](https://pbs.twimg.com/media/example.jpg)

完整文章内容（Markdown 格式）...

---

## 互动数据

- ❤️ 点赞: 206,351
- 🔁 转发: 28,631
- 👀 浏览: 115,555,283
- 🔖 书签: 571,495
```

**文件结构**: `{output_dir}/{username}/{tweet-id}.md`

## 工作原理

1. 从 URL 提取 tweet ID
2. 尝试 fxtwitter API（支持 Article）
3. 备选 syndication API
4. 解析并格式化输出
5. 自动保存为 Markdown 文件

## 限制

- 依赖第三方 API（fxtwitter），可能因服务变更而失效
- 私密账号的内容无法抓取
- 部分媒体内容可能无法获取完整 URL

## 依赖

- Python 3.6+
- requests >= 2.25.0

首次使用时会自动检查依赖，如果未安装会提示安装命令。

## Extension Support

通过 EXTEND.md 支持自定义配置。有关路径和支持的选项，请参阅 **Preferences** 部分。
