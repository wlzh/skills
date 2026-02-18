# X Fetcher Skill - 快速参考

## 🚀 快速开始

### 1. 安装依赖
```bash
cd /Users/m/document/QNSZ/project/skills/x-fetcher-skill
pip3 install -r scripts/requirements.txt
```

### 2. 运行配置脚本
```bash
bash scripts/quick-start.sh
```

### 3. 开始使用
```bash
python3 scripts/main.py "https://x.com/username/status/123456789"
```

## 📖 常用命令

| 命令 | 说明 |
|------|------|
| `python3 scripts/main.py <URL>` | 抓取推文并保存 |
| `python3 scripts/main.py --check-config` | 检查配置 |
| `python3 scripts/main.py <URL> --json` | 只输出 JSON |
| `python3 scripts/main.py <URL> --output <path>` | 指定输出目录 |
| `python3 scripts/test_skill.py` | 运行测试 |

## ⚙️ 配置文件

**位置**: `~/.x-fetcher/EXTEND.md`

```yaml
---
default_output_dir: ~/x-fetcher
auto_save: true
download_media: ask  # ask / true / false
---
```

### download_media 选项

| 值 | 说明 |
|----|------|
| `ask` | 每次询问是否下载媒体文件（默认） |
| `true` | 总是自动下载媒体到 imgs/ 和 videos/ |
| `false` | 从不下载，保留原始 URL |

## 📁 输出结构

```
~/x-fetcher/
└── {username}/
    └── {tweet-id}.md
```

## 📝 Markdown 格式

```markdown
# @username 的推文

> 作者: **Name** (@username)
> 发布时间: 2024-01-01 12:00:00
> 原文链接: https://x.com/user/status/123

---

推文内容...

---

## 互动数据

- ❤️ 点赞: 1,234
- 🔁 转发: 567
- 👀 浏览: 89,000
- 💬 回复: 123
```

## 🔗 支持的 URL

- `https://x.com/username/status/123456789`
- `https://twitter.com/username/status/123456789`

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 项目说明 |
| [USAGE.md](USAGE.md) | 详细使用指南 |
| [MEDIA.md](MEDIA.md) | 媒体文件下载说明 |
| [PROJECT.md](PROJECT.md) | 项目总结 |
| [COMPLETION.md](COMPLETION.md) | 完成报告 |

## ⚠️ 限制

- 依赖第三方 API（fxtwitter）
- 无法抓取私密账号内容
- 部分媒体 URL 可能不完整

## 🐛 故障排除

### 未找到配置文件
```bash
mkdir -p ~/.x-fetcher
cat > ~/.x-fetcher/EXTEND.md << 'EOF'
---
default_output_dir: ~/x-fetcher
---
EOF
```

### 依赖缺失
```bash
pip3 install -r scripts/requirements.txt
```

### 测试失败
```bash
python3 scripts/test_skill.py
```

## 📞 获取帮助

```bash
python3 scripts/main.py --help
bash scripts/quick-start.sh
cat USAGE.md
```

## 📄 License

MIT License - 基于 [Jane-xiaoer/x-fetcher](https://github.com/Jane-xiaoer/x-fetcher)

---

**项目位置**: `/Users/m/document/QNSZ/project/skills/x-fetcher-skill`
