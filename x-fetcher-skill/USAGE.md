# X Fetcher Skill 使用指南

## 概述

X Fetcher Skill 是一个基于 [Jane-xiaoer/x-fetcher](https://github.com/Jane-xiaoer/x-fetcher) 项目的命令行工具，用于抓取 X (Twitter) 推文和长文章，并自动保存为 Markdown 格式。

## 特色功能

- ✅ **自动保存**: 默认自动保存为 Markdown 文件
- ✅ **配置支持**: 支持通过配置文件设置默认下载目录
- ✅ **首次引导**: 如果没有配置文件，首次运行时会提示设置
- ✅ **灵活输出**: 支持 JSON 输出、自定义路径等多种选项
- ✅ **完整信息**: 包含推文内容、媒体链接、互动数据等

## 安装

### 1. 前置要求

- Python 3.6 或更高版本
- pip3

### 2. 安装依赖

```bash
cd /Users/m/document/QNSZ/project/skills/x-fetcher-skill
pip3 install -r scripts/requirements.txt
```

## 配置

### 快速配置

创建用户级配置文件：

```bash
mkdir -p ~/.x-fetcher
cat > ~/.x-fetcher/EXTEND.md << 'EOF'
---
default_output_dir: ~/Documents/x-posts
auto_save: true
download_media: ask
---
EOF
```

### 配置选项说明

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `default_output_dir` | 推文保存目录 | `./x-fetcher/` |
| `auto_save` | 自动保存 Markdown | `true` |
| `download_media` | 媒体文件处理 | `ask` |

## 使用

### 基本用法

```bash
cd /Users/m/document/QNSZ/project/skills/x-fetcher-skill
python3 scripts/main.py "https://x.com/username/status/123456789"
```

### 命令行选项

```bash
python3 scripts/main.py <URL> [选项]

选项:
  --output <path>      指定输出目录或文件路径
  --download-media     下载媒体文件到本地
  --json               只输出 JSON，不保存 Markdown
  --no-save            不保存 Markdown 文件
  --check-config       检查配置文件状态
```

### 使用示例

#### 1. 抓取推文（使用默认配置）

```bash
python3 scripts/main.py "https://x.com/elonmusk/status/123456789"
```

输出：
- JSON 格式的推文数据（到 stderr）
- Markdown 文件保存到配置的目录

#### 2. 指定输出目录

```bash
python3 scripts/main.py "https://x.com/elonmusk/status/123456789" --output ~/Downloads
```

#### 3. 只查看 JSON 数据

```bash
python3 scripts/main.py "https://x.com/elonmusk/status/123456789" --json
```

#### 4. 检查配置

```bash
python3 scripts/main.py --check-config
```

## 文件结构

### 输出文件命名规则

```
{output_dir}/{username}/{tweet-id}.md
```

示例：
```
~/Documents/x-posts/elonmusk/123456789.md
```

### Markdown 文件格式

#### 普通推文

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

#### X Article 长文章

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

## 集成到 Claude Code

### 安装为 Skill

将此目录链接到 Claude Code 的 skills 目录：

```bash
ln -s /Users/m/document/QNSZ/project/skills/x-fetcher-skill ~/.claude/skills/x-fetcher
```

### 在 Claude Code 中使用

直接向 Claude 提供推文 URL，Claude 会自动识别并调用此 Skill：

```
用户: 帮我下载这条推文 https://x.com/username/status/123456789
Claude: [调用 x-fetcher skill]
```

## 故障排除

### 1. 未找到配置文件

**错误信息**:
```
⚠️  未找到配置文件
请先设置默认下载目录。
```

**解决方案**:
创建配置文件：
```bash
mkdir -p ~/.x-fetcher
cat > ~/.x-fetcher/EXTEND.md << 'EOF'
---
default_output_dir: ~/Documents/x-posts
---
EOF
```

### 2. 依赖未安装

**错误信息**:
```
ModuleNotFoundError: No module named 'requests'
```

**解决方案**:
```bash
pip3 install -r scripts/requirements.txt
```

### 3. 抓取失败

**可能原因**:
- 推文已被删除
- 账号是私密账号
- 第三方 API 不可用

**解决方案**:
- 确认推文 URL 正确
- 确认推文是公开的
- 稍后重试

## 高级用法

### 批量抓取

创建脚本批量抓取多个推文：

```bash
#!/bin/bash
urls=(
  "https://x.com/user1/status/123"
  "https://x.com/user2/status/456"
  "https://x.com/user3/status/789"
)

for url in "${urls[@]}"; do
  python3 scripts/main.py "$url"
  sleep 2  # 避免请求过于频繁
done
```

### 与其他工具集成

结合其他工具处理抓取的内容：

```bash
# 抓取并转换为 HTML
python3 scripts/main.py "https://x.com/user/status/123" --json | jq '.content' > tweet.json

# 抓取并推送到 Git 仓库
python3 scripts/main.py "https://x.com/user/status/123"
git add x-fetcher/
git commit -m "Add new tweet"
git push
```

## 相关资源

- 原项目: https://github.com/Jane-xiaoer/x-fetcher
- Skills 文档: https://skills.sh/
- 问题反馈: 在原项目 GitHub Issues 中提交

## License

MIT License - 基于 [Jane-xiaoer/x-fetcher](https://github.com/Jane-xiaoer/x-fetcher) 项目
