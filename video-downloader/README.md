# 📹 YouTube Video Downloader

> 仓库地址: https://github.com/wlzh/skills
> **版本**: v1.0.0

Download YouTube videos with full control over quality and format settings.

## ✨ Features

- 🎬 **Multiple Quality Options** - Choose from best, 1080p, 720p, 480p, 360p, or worst quality
- 🎵 **Audio-Only Downloads** - Extract audio as MP3 with best quality
- 📦 **Multiple Formats** - Support for MP4, WebM, and MKV containers
- 🔄 **Auto-Installation** - Automatically installs yt-dlp if not present
- 📊 **Video Information** - Shows title, duration, and uploader before downloading
- 🎯 **Single Video Focus** - Downloads individual videos, skips playlists by default

## 🚀 Quick Start

The simplest way to download a video:

```bash
python scripts/download_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

This downloads the video in best available quality as MP4 to `/mnt/user-data/outputs/`.

## 📖 Usage

### Basic Download

```bash
# Download in best quality (default)
python scripts/download_video.py "https://youtu.be/dQw4w9WgXcQ"
```

### Quality Settings

Use `-q` or `--quality` to specify video quality:

```bash
# Download in 1080p
python scripts/download_video.py "URL" -q 1080p

# Download in 720p HD
python scripts/download_video.py "URL" -q 720p

# Download in lowest quality
python scripts/download_video.py "URL" -q worst
```

**Available quality options:**
- `best` (default) - Highest quality available
- `1080p` - Full HD
- `720p` - HD
- `480p` - Standard definition
- `360p` - Lower quality
- `worst` - Lowest quality available

### Format Options

Use `-f` or `--format` to specify output format (video downloads only):

```bash
# Download as WebM
python scripts/download_video.py "URL" -f webm

# Download as MKV
python scripts/download_video.py "URL" -f mkv
```

**Available formats:**
- `mp4` (default) - Most compatible
- `webm` - Modern format
- `mkv` - Matroska container

### Audio-Only Downloads

Use `-a` or `--audio-only` to download only audio as MP3:

```bash
# Download audio only
python scripts/download_video.py "URL" -a

# Audio downloads ignore quality and format settings
python scripts/download_video.py "URL" --audio-only
```

### Custom Output Directory

Use `-o` or `--output` to specify a different output directory:

```bash
# Save to custom directory
python scripts/download_video.py "URL" -o /path/to/directory

# Combine with other options
python scripts/download_video.py "URL" -q 720p -o ~/Downloads
```

## 📝 Complete Examples

**Download video in 1080p as MP4:**
```bash
python scripts/download_video.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -q 1080p
```

**Download audio only as MP3:**
```bash
python scripts/download_video.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -a
```

**Download in 720p as WebM to custom directory:**
```bash
python scripts/download_video.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -q 720p -f webm -o /custom/path
```

**Download best quality to specific folder:**
```bash
python scripts/download_video.py "https://youtu.be/dQw4w9WgXcQ" -o ~/Videos/YouTube
```

## 🔧 How It Works

The skill uses **yt-dlp**, a robust YouTube downloader that:

1. Automatically installs itself if not present
2. Fetches video information before downloading
3. Selects the best available streams matching your criteria
4. Merges video and audio streams when needed
5. Supports a wide range of YouTube video formats

### Technical Details

- **Video Downloads**: Selects best video and audio streams, then merges them
- **Audio Downloads**: Extracts audio and converts to MP3 format
- **Quality Selection**: Filters streams by resolution height (e.g., 720p = height ≤ 720)
- **Format Merging**: Uses ffmpeg to merge video and audio into specified container

## 📦 Dependencies

- **yt-dlp** - Automatically installed if not present
- **ffmpeg** - Required for merging streams (usually pre-installed)
- **Python 3.6+** - Required to run the script

## 🔄 Reusability

This skill is designed to be reusable by other skills:

**Used by:**
- `youtube-to-xiaoyuzhou` - Uses the audio-only download feature to get YouTube audio for podcast publishing

**Integration Example:**
```python
import subprocess

# Call from another skill
subprocess.run([
    "python3",
    "/path/to/video-downloader/scripts/download_video.py",
    youtube_url,
    "--audio-only",
    "--output", output_dir
], check=True)
```

## 📌 Important Notes

- Downloads are saved to `/mnt/user-data/outputs/` by default
- Video filename is automatically generated from the video title
- The script handles installation of yt-dlp automatically
- Only single videos are downloaded (playlists are skipped by default)
- Higher quality videos may take longer to download and use more disk space
- Audio-only downloads always use best quality and ignore format settings

## ⚠️ Limitations

- Playlists are not supported (use `--yes-playlist` flag manually if needed)
- Age-restricted videos may require authentication
- Some videos may not be available in all quality options
- Download speed depends on your internet connection and YouTube's servers

## 🐛 Troubleshooting

**yt-dlp not found:**
- The script will automatically install yt-dlp
- If installation fails, manually install: `pip install yt-dlp`

**ffmpeg not found:**
- Install ffmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)

**Video unavailable:**
- Check if the video is public and accessible
- Try a different quality setting
- Verify the URL is correct

**Download fails:**
- Check your internet connection
- Try updating yt-dlp: `pip install --upgrade yt-dlp`
- Some videos may have regional restrictions

## 📄 License

Personal project, for educational and personal use only.

## 🙏 Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful YouTube downloader
- [ffmpeg](https://ffmpeg.org/) - Multimedia framework for stream processing

---

**Quick Start**: `python scripts/download_video.py "YOUTUBE_URL"` 🚀
