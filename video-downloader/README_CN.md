# 📹 YouTube 视频下载器

下载 YouTube 视频，完全控制质量和格式设置。

## ✨ 功能特点

- 🎬 **多种质量选项** - 可选择最佳、1080p、720p、480p、360p 或最低质量
- 🎵 **纯音频下载** - 提取音频为最佳质量的 MP3 格式
- 📦 **多种格式支持** - 支持 MP4、WebM 和 MKV 容器格式
- 🔄 **自动安装依赖** - 如果未安装 yt-dlp 会自动安装
- 📊 **视频信息显示** - 下载前显示标题、时长和上传者信息
- 🎯 **单视频下载** - 下载单个视频，默认跳过播放列表

## 🚀 快速开始

最简单的下载方式：

```bash
python scripts/download_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

这将以最佳质量下载视频为 MP4 格式，保存到 `/mnt/user-data/outputs/` 目录。

## 📖 使用方法

### 基础下载

```bash
# 以最佳质量下载（默认）
python scripts/download_video.py "https://youtu.be/dQw4w9WgXcQ"
```

### 质量设置

使用 `-q` 或 `--quality` 指定视频质量：

```bash
# 下载 1080p 视频
python scripts/download_video.py "URL" -q 1080p

# 下载 720p 高清视频
python scripts/download_video.py "URL" -q 720p

# 下载最低质量
python scripts/download_video.py "URL" -q worst
```

**可用的质量选项：**
- `best`（默认）- 最高可用质量
- `1080p` - 全高清
- `720p` - 高清
- `480p` - 标清
- `360p` - 较低质量
- `worst` - 最低可用质量

### 格式选项

使用 `-f` 或 `--format` 指定输出格式（仅视频下载）：

```bash
# 下载为 WebM 格式
python scripts/download_video.py "URL" -f webm

# 下载为 MKV 格式
python scripts/download_video.py "URL" -f mkv
```

**可用格式：**
- `mp4`（默认）- 兼容性最好
- `webm` - 现代格式
- `mkv` - Matroska 容器

### 纯音频下载

使用 `-a` 或 `--audio-only` 仅下载音频为 MP3 格式：

```bash
# 仅下载音频
python scripts/download_video.py "URL" -a

# 音频下载会忽略质量和格式设置
python scripts/download_video.py "URL" --audio-only
```

### 自定义输出目录

使用 `-o` 或 `--output` 指定不同的输出目录：

```bash
# 保存到自定义目录
python scripts/download_video.py "URL" -o /path/to/directory

# 与其他选项组合使用
python scripts/download_video.py "URL" -q 720p -o ~/Downloads
```

## 📝 完整示例

**下载 1080p MP4 视频：**
```bash
python scripts/download_video.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -q 1080p
```

**仅下载音频为 MP3：**
```bash
python scripts/download_video.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -a
```

**下载 720p WebM 格式到自定义目录：**
```bash
python scripts/download_video.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -q 720p -f webm -o /custom/path
```

**下载最佳质量到指定文件夹：**
```bash
python scripts/download_video.py "https://youtu.be/dQw4w9WgXcQ" -o ~/Videos/YouTube
```

## 🔧 工作原理

本工具使用 **yt-dlp**，一个强大的 YouTube 下载器：

1. 如果未安装会自动安装
2. 下载前获取视频信息
3. 选择符合条件的最佳可用流
4. 必要时合并视频和音频流
5. 支持广泛的 YouTube 视频格式

### 技术细节

- **视频下载**：选择最佳视频和音频流，然后合并
- **音频下载**：提取音频并转换为 MP3 格式
- **质量选择**：按分辨率高度过滤流（例如 720p = 高度 ≤ 720）
- **格式合并**：使用 ffmpeg 将视频和音频合并到指定容器

## 📦 依赖项

- **yt-dlp** - 如未安装会自动安装
- **ffmpeg** - 合并流所需（通常已预装）
- **Python 3.6+** - 运行脚本所需

## 🔄 可重用性

本工具设计为可被其他工具重用：

**被以下工具使用：**
- `youtube-to-xiaoyuzhou` - 使用纯音频下载功能获取 YouTube 音频用于播客发布

**集成示例：**
```python
import subprocess

# 从其他工具调用
subprocess.run([
    "python3",
    "/path/to/video-downloader/scripts/download_video.py",
    youtube_url,
    "--audio-only",
    "--output", output_dir
], check=True)
```

## 📌 重要说明

- 默认下载保存到 `/mnt/user-data/outputs/` 目录
- 视频文件名自动从视频标题生成
- 脚本会自动处理 yt-dlp 的安装
- 默认只下载单个视频（跳过播放列表）
- 更高质量的视频下载时间更长，占用磁盘空间更大
- 纯音频下载始终使用最佳质量，忽略格式设置

## ⚠️ 限制

- 不支持播放列表（如需要可手动使用 `--yes-playlist` 标志）
- 年龄限制视频可能需要身份验证
- 某些视频可能不提供所有质量选项
- 下载速度取决于您的网络连接和 YouTube 服务器

## 🐛 故障排除

**找不到 yt-dlp：**
- 脚本会自动安装 yt-dlp
- 如果安装失败，手动安装：`pip install yt-dlp`

**找不到 ffmpeg：**
- 安装 ffmpeg：`brew install ffmpeg`（macOS）或 `apt install ffmpeg`（Linux）

**视频不可用：**
- 检查视频是否公开且可访问
- 尝试不同的质量设置
- 验证 URL 是否正确

**下载失败：**
- 检查网络连接
- 尝试更新 yt-dlp：`pip install --upgrade yt-dlp`
- 某些视频可能有地区限制

## 📄 许可证

个人项目，仅供学习和个人使用。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的 YouTube 下载工具
- [ffmpeg](https://ffmpeg.org/) - 多媒体处理框架

---

**快速开始**：`python scripts/download_video.py "YOUTUBE_URL"` 🚀
