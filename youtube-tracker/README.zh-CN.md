# youtube-tracker（YouTube 频道新视频追踪）

定时追踪一组 YouTube 频道是否有**新视频上传**。

- 维护本地“频道列表”
- 周期性拉取每个频道最新视频
- **没更新就不输出**（非常适合接 OpenClaw cron：有内容才推送到群/话题）

---

## ✅ 输出格式

检测到新视频时，每条新视频输出 4 行：

- 频道：<频道名字>
- 标题：<视频标题>
- 简介：<简介摘要>
- 链接：<视频 URL>

多条视频之间用空行分隔。

---

## ✅ 依赖

- Node.js 18+（建议 Node 20+）
- YouTube Data API v3 的 **API Key**

---

## 🔑 如何获取 YouTube API Key（YouTube Data API v3）

1. 打开 Google Cloud Console：
   https://console.cloud.google.com/
2. 创建/选择一个项目（Project）
3. 进入 **API 和服务 → 库**，启用：**YouTube Data API v3**
4. 进入 **API 和服务 → 凭据（Credentials）**
5. 创建 **API Key** 并复制

建议：如果条件允许，给 key 做限制（IP / Referrer），更安全。

---

## 📁 配置与状态文件

本 skill 的本地状态都在 `state/` 目录下（**不提交到 git**）：

### 1) `state/config.json`（本地配置）

```json
{
  "apiKey": "YOUR_KEY",
  "channels": [
    {
      "channelId": "UCxxxxxxxxxxxxxxxxxxxxxx",
      "title": "频道名",
      "handle": "@handle",
      "addedAt": "2026-03-13T00:00:00.000Z"
    }
  ]
}
```

字段说明：
- `apiKey`：你的 YouTube Data API v3 key
- `channels[]`：追踪的频道列表（add 时自动写入）
- `addedAt`：该频道被加入的时间（用于 baseline 防刷屏）

### 2) `state/seen.json`（去重/已播报记录）

```json
{
  "seenVideoIds": ["VIDEO_ID_1", "VIDEO_ID_2"],
  "updatedAt": "2026-03-13T00:00:00.000Z"
}
```

仓库里只会提供示例文件：
- `state/config.json.example`
- `state/seen.json.example`

---

## 🧰 命令用法

进入本目录执行：

```bash
cd youtube-tracker
```

### 1) 设置 Key（3 种方式）

```bash
# 方式 A：参数
node scripts/youtube-tracker.js set-key "YOUR_KEY"

# 方式 B：环境变量
YOUTUBE_API_KEY="YOUR_KEY" node scripts/youtube-tracker.js set-key

# 方式 C：stdin
echo "YOUR_KEY" | node scripts/youtube-tracker.js set-key
```

### 2) 验证 Key

```bash
node scripts/youtube-tracker.js validate-key
```

### 3) 添加频道（支持 @handle / URL / channelId）

```bash
node scripts/youtube-tracker.js add "@veritasium"
node scripts/youtube-tracker.js add "https://www.youtube.com/@veritasium"
node scripts/youtube-tracker.js add "https://www.youtube.com/channel/UCddiUEpeqJcYeBxX1IVBKvQ"
node scripts/youtube-tracker.js add "UCddiUEpeqJcYeBxX1IVBKvQ"
```

### 4) 列出 / 删除频道

```bash
node scripts/youtube-tracker.js list

# remove 支持传 @handle / URL / channelId
node scripts/youtube-tracker.js remove "@veritasium"
node scripts/youtube-tracker.js remove "UCddiUEpeqJcYeBxX1IVBKvQ"
```

### 5) 检查新视频（只输出新增）

```bash
node scripts/youtube-tracker.js check
```

- 没新视频：不输出任何内容（exit code 0）
- 有新视频：按“输出格式”打印

---

## 🛡️ Baseline（避免首次刷屏历史视频）

新加入频道后：
- 系统会以 `addedAt` 为基线
- `check` 只会把 **发布时间晚于 `addedAt`** 的视频视为“新视频”

目的：避免你第一次加频道时，把该频道历史视频一次性刷出来。

---

## ⏱️ OpenClaw / Cron 接法（推荐姿势）

cron 每次执行：

1. 跑：`node scripts/youtube-tracker.js check`
2. stdout 为空 → 什么都不做
3. stdout 非空 → 把 stdout 整段发到目标群/话题

（这样你群里只有“真的有更新”才会出现消息）
