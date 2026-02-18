# 媒体文件下载功能说明

## 概述

X Fetcher Skill 支持下载推文中的媒体文件（图片和视频）到本地，并自动更新 Markdown 文件中的链接。

## 配置选项

在 `EXTEND.md` 配置文件中，`download_media` 选项支持三种模式：

### 1. `ask` - 每次询问（默认）

```yaml
---
download_media: ask
---
```

**行为**：
- 抓取推文后，如果发现有媒体文件，会询问是否下载
- 用户可以选择 `y`（下载）或 `n`（不下载）

**适用场景**：
- 想要根据具体情况决定是否下载
- 节省存储空间

### 2. `true` - 总是下载

```yaml
---
download_media: true
---
```

或

```yaml
---
download_media: 1
---
```

**行为**：
- 自动下载所有媒体文件到本地
- 不需要用户确认

**适用场景**：
- 离线查看推文内容
- 归档重要的媒体资源
- 网络不稳定的环境

### 3. `false` - 从不下载

```yaml
---
download_media: false
---
```

或

```yaml
---
download_media: 0
---
```

**行为**：
- 保留原始远程 URL
- 不下载任何媒体文件

**适用场景**：
- 只需要保存文本内容
- 节省存储空间
- 快速抓取大量推文

## 媒体文件存储

### 目录结构

下载的媒体文件会保存在以下结构中：

```
{output_dir}/{username}/
├── {tweet-id}.md        # Markdown 文件
├── imgs/                # 图片目录
│   ├── {tweet-id}_img1.jpg
│   ├── {tweet-id}_img2.png
│   └── ...
└── videos/              # 视频目录
    ├── {tweet-id}_video1.mp4
    ├── {tweet-id}_video2.mov
    └── ...
```

### 示例

如果下载 Elon Musk 的推文 `123456789`：

```
~/x-fetcher/
└── elonmusk/
    ├── 123456789.md
    ├── imgs/
    │   ├── 123456789_img1.jpg
    │   └── 123456789_img2.jpg
    └── videos/
        └── 123456789_video1.mp4
```

## Markdown 链接更新

### 原始 Markdown（未下载媒体）

```markdown
## 媒体

![媒体1](https://pbs.twimg.com/media/example.jpg)
![媒体2](https://pbs.twimg.com/media/example2.jpg)
```

### 更新后 Markdown（已下载媒体）

```markdown
## 媒体

![媒体1](imgs/123456789_img1.jpg)
![媒体2](imgs/123456789_img2.jpg)
```

## 支持的媒体格式

### 图片
- `.jpg` / `.jpeg`
- `.png`
- `.gif`
- `.webp`

### 视频
- `.mp4`
- `.mov`
- `.webm`

## 命令行覆盖

即使配置文件中设置了 `download_media`，也可以通过命令行参数覆盖：

```bash
# 强制下载媒体文件
python3 scripts/main.py "https://x.com/user/status/123" --download-media

# 即使配置为 true，也不会下载（因为没有媒体或通过 --json 输出）
python3 scripts/main.py "https://x.com/user/status/123" --json
```

## 使用示例

### 示例 1: 询问模式

```bash
$ python3 scripts/main.py "https://x.com/user/status/123"

📍 Tweet ID: 123
📍 Username: user
🔍 正在抓取...
  ✅ fxtwitter 成功

📎 发现 3 个媒体文件
是否下载媒体文件到本地？(y/n): y

📥 开始下载媒体文件...
  📥 正在下载: 123_img1.jpg
  ✅ 已下载: 123_img1.jpg
  📥 正在下载: 123_img2.jpg
  ✅ 已下载: 123_img2.jpg
  📥 正在下载: 123_video1.mp4
  ✅ 已下载: 123_video1.mp4
✅ 已下载 3 个媒体文件

✅ Markdown 已保存到: ~/x-fetcher/user/123.md
```

### 示例 2: 自动下载模式

```yaml
# ~/.x-fetcher/EXTEND.md
---
download_media: true
---
```

```bash
$ python3 scripts/main.py "https://x.com/user/status/123"

📍 Tweet ID: 123
📍 Username: user
🔍 正在抓取...
  ✅ fxtwitter 成功

📥 开始下载媒体文件...
  📥 正在下载: 123_img1.jpg
  ✅ 已下载: 123_img1.jpg
  📥 正在下载: 123_img2.jpg
  ✅ 已下载: 123_img2.jpg
✅ 已下载 2 个媒体文件

✅ Markdown 已保存到: ~/x-fetcher/user/123.md
💡 提示: 媒体文件保留为远程 URL
```

### 示例 3: 不下载模式

```yaml
# ~/.x-fetcher/EXTEND.md
---
download_media: false
---
```

```bash
$ python3 scripts/main.py "https://x.com/user/status/123"

📍 Tweet ID: 123
📍 Username: user
🔍 正在抓取...
  ✅ fxtwitter 成功

✅ Markdown 已保存到: ~/x-fetcher/user/123.md
```

## 注意事项

1. **存储空间**: 媒体文件可能占用大量存储空间，建议根据需要选择合适的下载模式
2. **下载速度**: 下载大量媒体文件可能需要较长时间
3. **网络连接**: 下载需要稳定的网络连接
4. **版权问题**: 下载的媒体文件仅供个人使用，请遵守版权法规
5. **失败处理**: 如果单个文件下载失败，会跳过并继续下载其他文件

## 故障排除

### 媒体文件下载失败

**可能原因**：
- 网络连接问题
- 文件已被删除
- 权限问题

**解决方案**：
1. 检查网络连接
2. 重试抓取
3. 手动下载失败的文件

### 媒体链接未更新

**可能原因**：
- 配置设置为 `false` 或 `ask` 时选择了 `n`

**解决方案**：
1. 修改配置为 `download_media: true`
2. 重新抓取推文
3. 使用 `--download-media` 参数

## 配置示例

### 完整配置示例

```yaml
---
default_output_dir: ~/Documents/x-archive
auto_save: true
download_media: true
---
```

### 最小配置示例

```yaml
---
default_output_dir: ~/x-fetcher
download_media: ask
---
```

## 相关文档

- [配置文件说明](EXTEND.md.example)
- [使用指南](USAGE.md)
- [快速参考](QUICKREF.md)
