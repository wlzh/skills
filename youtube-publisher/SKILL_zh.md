# YouTube 视频上传工具

> **首次使用？** 如果上面 `setup_complete: false`，请先运行 `./SETUP.md` 进行设置，然后将 `SKILL.md` 中的 `setup_complete` 改为 `true`。

使用完整元数据控制将视频上传到 YouTube。

## YouTube Live 直播管理

使用 `youtube-live.ts` 创建、查询、更新、绑定、切换状态和删除直播活动与编码器推流。
所有修改操作应先使用 `--dry-run` 预览；删除、切换为直播/结束状态，以及显示推流密钥时必须显式传入 `--yes`。
普通输出会自动隐藏推流密钥。完整命令和安全规则见 [references/live-streaming.md](references/live-streaming.md)。
默认情况下，每个独立节目或活动使用单独命名的编码器推流；如需在多个活动间有意复用，必须传入 `--allow-shared-stream`。

视频上传响应中断后，`youtube-upload.ts` 内部不得再次盲目 insert。持续 `P0D` 使用退出码 42 和 `PERSISTENT_P0D_VIDEO_ID`；服务端检查为空、异常或无法确认时使用退出码 43 和 `AMBIGUOUS_UPLOAD_VIDEO_ID`，必须先核对频道再重传。
字幕恢复对同语言/名称轨道执行原位更新，不得先删除现有字幕。

## 元数据清洗规则

- 标题/详情里的 `>` 会自动改写成 `》`
- 标题/详情里的 `<` 会自动改写成 `《`
- 当 YouTube 因特殊字符拒绝元数据时，优先使用这个规则

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

### 仅补传失败的封面图

视频已经存在、只有自定义封面上传失败时，使用专用恢复命令。命令会校验视频
ID 和本地 JPG/PNG 文件，有限次数重试临时错误，确认目标视频可读取，并输出
可供流水线判断的结构化结果。

```bash
npx ts-node upload-thumbnail.ts \
  --video-id 视频ID \
  --thumbnail /path/to/cover.jpg \
  --attempts 3
```

此命令不会删除或上传视频。禁止再创建带固定视频 ID 或本地绝对路径的一次性
恢复脚本。

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
| EPIPE 上传失败 | v1.1 已修复，自动重试 3 次。如仍失败，检查网络稳定性 |
| 封面图上传失败 | 检查图片格式是否为 JPG/PNG，大小不超过 2MB |
| 字幕上传失败 | 重新运行 `--auth` 重新授权，确保 API 权限完整 |
| 配额超限 | 在 Google Cloud Console 查看配额 |
| 权限被拒绝 | 重新授权：`npx ts-node youtube-upload.ts --auth` |

上传进程报错且无法确认服务端是否已创建视频时，先运行以下命令查看最近上传记录，再决定是否重试，避免生成重复视频：

```bash
npx ts-node list-uploads.ts
```

## 更新日志

### v1.6.0 - 安全的封面单独补传 (2026-07-28)

- 新增 `upload-thumbnail.ts`，包含参数校验、有限重试、目标视频验证和结构化输出。
- 删除会操作固定视频 ID、同时带删除动作的硬编码封面修复脚本。
- 将封面恢复命令纳入生产 TypeScript 严格检查。

### v1.5.0 - 上传恢复与重复检测 (2026-07-21)

- 修复网络错误恢复分支错误传递 SearchResult 对象的问题，改为使用真实 `videoId`。
- 新增 `list-uploads.ts`，供发布流水线在上传失败后检查同标题视频。
- 新增生产脚本 TypeScript 严格检查命令。

### v1.1 - 可恢复上传 + 自动重试 (2026-04-22)

- 修复大文件上传 EPIPE 错误，改用可恢复上传并添加进度跟踪
- 新增自动重试机制（最多 3 次），针对 EPIPE、ETIMEDOUT、ECONNRESET 等网络错误
- 新增上传进度日志（每 10% 输出一次）
- 添加 `media.mimeType` 提升上传兼容性

### v1.0 - 初始版本

- 基础视频上传及元数据设置
- 封面图、字幕、播放列表支持
- OAuth2 认证
