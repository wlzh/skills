# YouTube 视频上传工具

> **首次使用？** 如果上面 `setup_complete: false`，请先运行 `./SETUP.md` 进行设置，然后将 `SKILL.md` 中的 `setup_complete` 改为 `true`。

使用完整元数据控制将视频上传到 YouTube。

## 快速开始

```bash
cd ~/.claude/skills/youtube-publisher/scripts

# 首次使用：进行身份验证
npx ts-node youtube-upload.ts --auth

# 上传视频
npx ts-node youtube-upload.ts \
  --video /path/to/video.mp4 \
  --title "我的视频标题" \
  --description "视频描述内容" \
  --tags "标签1,标签2,标签3" \
  --privacy public
```

## 参数说明

| 参数 | 简写 | 说明 |
|------|------|------|
| `--video` | `-v` | 视频文件路径（必填） |
| `--title` | `-t` | 视频标题（必填） |
| `--description` | `-d` | 视频描述 |
| `--tags` | | 标签，逗号分隔 |
| `--privacy` | `-p` | 隐私设置：public, unlisted, private（默认：unlisted） |
| `--category` | `-c` | 分类 ID（默认：22 = 生活） |
| `--thumbnail` | | 封面图片路径（本地路径或 URL） |
| `--subtitles` | | 字幕文件路径（SRT/VTT） |
| `--subtitle-lang` | | 字幕语言代码（默认：zh） |
| `--subtitle-name` | | 字幕显示名称（默认：中文） |
| `--playlist` | | 添加到播放列表 ID |
| `--short` | | 标记为 YouTube Short（短视频） |
| `--auth` | | 运行 OAuth2 身份验证 |
| `--dry-run` | | 预览而不实际上传 |

## 分类 ID

| ID | 分类 |
|----|------|
| 1 | 电影与动画 |
| 2 | 汽车与交通工具 |
| 10 | 音乐 |
| 15 | 宠物与动物 |
| 17 | 体育 |
| 19 | 旅行与活动 |
| 20 | 游戏 |
| 22 | 生活 |
| 23 | 喜剧 |
| 24 | 娱乐 |
| 25 | 新闻与政治 |
| 26 | 时尚 |
| 27 | 教育 |
| 28 | 科学与技术 |

## 环境配置

创建 `scripts/.env` 文件：

```env
YOUTUBE_CLIENT_ID=你的客户端ID
YOUTUBE_CLIENT_SECRET=你的客户端密钥
```

从 Google Cloud Console 获取凭据：
1. 访问 console.cloud.google.com
2. 创建项目并启用 YouTube Data API v3
3. 创建 OAuth2 凭据（选择 **Desktop app**，即桌面应用）
4. 下载并获取 client_id 和 client_secret

## 使用示例

### 上传普通视频

```bash
npx ts-node youtube-upload.ts \
  -v tutorial.mp4 \
  -t "完整教程视频" \
  -d "这是一个详细的教程视频

时间戳：
00:00 开场介绍
02:30 基础内容
05:00 进阶技巧

#教程 #学习" \
  --tags "教程,学习,技术" \
  --privacy public
```

### 上传 YouTube Short（短视频）

```bash
npx ts-node youtube-upload.ts \
  -v short_video.mp4 \
  -t "技巧分享 #Shorts" \
  --privacy public \
  --short
```

### 上传到播放列表

```bash
npx ts-node youtube-upload.ts \
  -v episode5.mp4 \
  -t "第5期节目" \
  --playlist 播放列表ID \
  --privacy unlisted
```

### 上传并设置封面和字幕

```bash
npx ts-node youtube-upload.ts \
  -v video.mp4 \
  -t "带字幕的视频教程" \
  -d "详细的中文字幕教程" \
  --thumbnail "/Users/m/Downloads/shell/work/cover.jpg" \
  --subtitles "/Users/m/Downloads/shell/work/subtitles.srt" \
  --subtitle-lang zh \
  --subtitle-name "中文" \
  --privacy public
```

### 使用本地封面图

```bash
npx ts-node youtube-upload.ts \
  -v video.mp4 \
  -t "我的视频标题" \
  --thumbnail "/Users/m/Downloads/shell/work/cover.jpg" \
  --privacy public
```

## 输出结果

上传成功后返回：
- 视频 ID
- 视频链接 (https://youtu.be/视频ID)
- 状态

## 限制说明

- 最大文件大小：256GB（YouTube 限制）
- 支持格式：MP4, MOV, AVI, WMV, FLV, 3GP, MPEG
- 支持字幕格式：SRT, VTT
- 每日上传配额：10,000 单位（通常约 6 个视频/天）
- 标题最大：100 个字符
- 描述最大：5,000 个字符
- 标签最大：500 个字符

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 封面图上传失败 | 检查图片格式是否为 JPG/PNG，大小不超过 2MB |
| 字幕上传失败 | 重新运行 `--auth` 重新授权，确保 API 权限完整 |
| 配额超限 | 在 Google Cloud Console 查看配额 |
| 权限被拒绝 | 重新授权：`npx ts-node youtube-upload.ts --auth` |
