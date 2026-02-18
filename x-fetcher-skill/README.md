# X Fetcher Skill

抓取 X (Twitter) 推文和长文章的命令行工具，支持自动保存为 Markdown 格式。

**工程化来源**: 本 Skill 基于 [Jane-xiaoer/x-fetcher](https://github.com/Jane-xiaoer/x-fetcher) 项目。

## 功能特性

- ✅ 抓取普通推文（文字、图片、视频链接）
- ✅ 抓取 X Article 长文章（完整正文，Markdown 格式）
- ✅ 获取互动数据（点赞、转发、浏览量、书签数）
- ✅ 自动保存为格式化的 Markdown 文件
- ✅ 可配置默认下载目录
- ✅ 支持配置文件（项目级或用户级）
- ✅ **媒体文件下载**（图片/视频下载到本地，自动更新 Markdown 链接）

## 快速开始

### 1. 安装依赖

```bash
pip3 install -r scripts/requirements.txt
```

### 2. 配置（首次使用）

创建配置文件 `~/.x-fetcher/EXTEND.md`（用户级）或 `.x-fetcher/EXTEND.md`（项目级）:

```yaml
---
default_output_dir: ~/Documents/x-posts
auto_save: true
download_media: ask
---
```

### 3. 使用

```bash
python3 scripts/main.py "https://x.com/username/status/123456789"
```

## 使用示例

### 基本用法

```bash
# 抓取推文并自动保存到配置的目录
python3 scripts/main.py "https://x.com/elonmusk/status/123456789"

# 指定输出目录
python3 scripts/main.py "https://x.com/elonmusk/status/123456789" --output ~/Downloads

# 只输出 JSON，不保存 Markdown
python3 scripts/main.py "https://x.com/elonmusk/status/123456789" --json

# 不保存 Markdown 文件
python3 scripts/main.py "https://x.com/elonmusk/status/123456789" --no-save
```

### 检查配置

```bash
python3 scripts/main.py --check-config
```

## 媒体文件下载

X Fetcher 支持三种媒体文件处理模式：

### 1. 询问模式（默认）

```yaml
download_media: ask
```

每次发现媒体文件时询问是否下载。

### 2. 自动下载

```yaml
download_media: true
```

自动下载所有媒体文件到本地 `imgs/` 和 `videos/` 目录。

### 3. 从不下载

```yaml
download_media: false
```

保留原始远程 URL，不下载媒体文件。

详细说明请查看 [MEDIA.md](MEDIA.md)。

## 配置说明

配置文件支持以下选项：

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `default_output_dir` | string | `./x-fetcher/` | 默认输出目录 |
| `auto_save` | boolean | `true` | 自动保存 Markdown 文件 |
| `download_media` | string/boolean | `ask` | 媒体文件处理方式（`ask`/`true`/`false`） |

### 配置文件位置

优先级（从高到低）：
1. **项目级**: `.x-fetcher/EXTEND.md`（在当前工作目录）
2. **用户级**: `~/.x-fetcher/EXTEND.md`（在用户主目录）

## 输出示例

### 普通推文

文件路径: `{output_dir}/{username}/{tweet-id}.md`

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

文件路径: `{output_dir}/{username}/{tweet-id}.md`

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

## 工作原理

1. 从 URL 提取 tweet ID
2. 尝试 fxtwitter API（支持 Article）
3. 备选 syndication API
4. 解析并格式化输出
5. 自动保存为 Markdown 文件

## 限制

- ⚠️ 依赖第三方 API（fxtwitter），可能因服务变更而失效
- ⚠️ 私密账号的内容无法抓取
- ⚠️ 部分媒体内容可能无法获取完整 URL

## 依赖

- Python 3.6+
- requests >= 2.25.0
- PyYAML >= 5.4

## License

本 Skill 基于原项目的 MIT License。

## 致谢

本 Skill 是对 [Jane-xiaoer/x-fetcher](https://github.com/Jane-xiaoer/x-fetcher) 项目的封装和增强，感谢原作者的贡献。

## 相关链接

- 原项目: https://github.com/Jane-xiaoer/x-fetcher
- Skills 文档: https://skills.sh/
