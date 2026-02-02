# YouTube 转博客文章 Skill - 创建完成

## ✅ 已创建的文件

### Skill 文件（`~/.claude/skills/youtube-to-blog-post/`）
```
youtube-to-blog-post/
├── SKILL.md                    # Skill 定义和说明
├── README.md                   # 详细使用文档
└── scripts/
    └── youtube_to_post.py      # 核心脚本
```

### 博客配置文件（`/path/to/myblog/`）
```
myblog/
├── youtube-blog-config.json    # 配置文件
├── YOUTUBE_TO_POST_GUIDE.md    # 快速使用指南
└── README.md                   # 已更新（添加 YouTube 转文章说明）
```

## 🎯 功能特性

### 核心功能
- ✅ 自动获取 YouTube 视频信息（标题、描述、时长、作者）
- ✅ 智能生成英文文件名（kebab-case）
- ✅ 生成符合 Hexo 博客格式的文章
- ✅ 在文章开头嵌入 YouTube 视频播放器（首屏可见）
- ✅ 自动生成文章摘要、内容、参考链接
- ✅ 支持自定义配置文件

### 智能特性
- 📝 中文标题自动转英文文件名
- 🔗 支持多种 YouTube URL 格式
- ⚡ 自动提取视频时间戳章节
- 🎨 自动生成关键词和描述
- 📅 自动使用视频上传日期

## 📖 使用方法

### 基本用法
```bash
python ~/.claude/skills/youtube-to-blog-post/scripts/youtube_to_post.py "YouTube_URL"
```

### 指定分类和标签
```bash
python ~/.claude/skills/youtube-to-blog-post/scripts/youtube_to_post.py \
  "YouTube_URL" \
  -c "技术" \
  -t "AI工具 教程"
```

### 预览模式
```bash
python ~/.claude/skills/youtube-to-blog-post/scripts/youtube_to_post.py \
  "YouTube_URL" --dry-run
```

## 📋 配置文件

在博客根目录的 `youtube-blog-config.json`：

```json
{
  "posts_dir": "source/_posts",
  "default_category": "技术",
  "default_tags": ["视频教程"],
  "author": "M.",
  "image_cdn": "https://img.869hr.uk"
}
```

## 📝 生成的文章格式

```markdown
---
title: 视频标题
subtitle: 视频标题
date: 2026-01-27 23:30:00
updated: 2026-01-27 23:30:00
author: M.
description: 视频描述...
categories:
  - 技术
tags:
  - 视频教程
keywords:
  - 关键词
toc: true
comments: true
copyright: true
---

<!-- 文章摘要 -->
{% blockquote %}
视频摘要...
{% endblockquote %}

## 视频教程
<iframe src="https://www.youtube.com/embed/VIDEO_ID"></iframe>

## 视频介绍
...

## 内容详解
...

## 参考链接
...
```

## 🎬 文件名示例

| 视频标题 | 生成的文件名 |
|----------|-------------|
| 🔥【窗口期速抢】真正的永久免费域名 | `freedomainregister10free-cloudflare.md` |
| AI代理学习完整教程 | `ai-agent-study-tutorial.md` |
| 免费域名申请指南 | `free-domain-apply-guide.md` |
| UUID生成器使用 | `uuid-generator-usage.md` |

## 🚀 完整工作流

```bash
# 1. 进入博客目录
cd /path/to/myblog

# 2. 从 YouTube 生成文章
python ~/.claude/skills/youtube-to-blog-post/scripts/youtube_to_post.py \
  "https://www.youtube.com/watch?v=xxxxx"

# 3. 本地预览
hexo cl; hexo s

# 4. 部署上线
hexo cl; hexo g; hexo d
```

## ✅ 测试结果

已成功测试（`--dry-run` 模式）：
- ✅ 获取视频信息正常
- ✅ 生成英文文件名正常
- ✅ 生成文章格式符合要求
- ✅ YouTube iframe 嵌入正确
- ✅ 文章摘要、内容生成正常

## 📚 相关文档

- [Skill 详细说明](~/.claude/skills/youtube-to-blog-post/README.md)
- [快速使用指南](./YOUTUBE_TO_POST_GUIDE.md)
- [博客 README](./README.md)
- [技术文档](./CLAUDE.md)

## 🎉 下一步

1. **使用 Skill 工具调用**：可以直接使用 `/youtube-to-blog-post` 命令
2. **自定义模板**：根据需要编辑 `youtube_to_post.py` 中的内容生成函数
3. **批量处理**：创建 shell 脚本批量处理多个视频

## 🔧 技术细节

- **语言**: Python 3
- **依赖**: yt-dlp, requests
- **支持平台**: macOS, Linux, Windows
- **URL 格式**: 所有标准 YouTube URL 格式

---

**创建时间**: 2026-02-02
**版本**: 1.0.0
**状态**: ✅ 已测试并可用
