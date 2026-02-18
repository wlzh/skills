# skills

Claude Code Skills 集合 - 各种实用工具和自动化脚本的集合

## 📚 Skills 列表

### 🎙️ youtube-to-xiaoyuzhou
YouTube 视频自动下载并发布到小宇宙播客

**特点**：
- 📥 自动下载 YouTube 视频/音频
- 🔍 AI 生成封面图片（image-generator）
- ✂️ 关键字过滤（audiocut-keyword）
- 🎤 音频变声处理（voice-changer）
- 📅 定时发布支持
- 🍪 Cookie 优先登录验证

**适用场景**：播客自动化、内容分发、YouTube 转播客

---

### 🎵 voice-changer
音频变声处理工具 - 使用 RVC AI 模型进行真实的声音转换

**特点**：
- 🎙️ RVC AI 模型 - 真实的音色转换（不只是音高调整）
- ⚡ 自动分块处理 - 长音频自动分块，避免内存问题
- 🔧 灵活配置 - 支持多种声音预设和自定义参数
- 🌐 多语言支持 - 中文御姐、七妹、苏苏、AZI 等声音
- 🔌 可被调用 - 可被其他 skills 集成调用

**版本**: v1.5.0

[查看详情 →](./voice-changer/)

---

### 🎬 video-voice-changer
视频变声处理工具 - 对视频中的音频进行变声处理后重新合并

**特点**：
- 🎙️ 视频音频提取与变声
- 🎵 复用 voice-changer 多种声音预设
- 📹 保持原视频质量（仅替换音频）
- 🛡️ 默认不覆盖原文件（创建新文件）
- 🧹 临时文件自动清理

**版本**: v1.1.0

[查看详情 →](./video-voice-changer/)

---

### ✂️ audiocut-keyword
音频关键字过滤工具 - 根据关键字配置自动识别并删除音频中的指定内容

**特点**：
- 🎤 精确转录（FunASR Paraformer，字符级时间戳）
- 🔍 关键字识别（根据配置文件自动识别）
- ✂️ 智能剪辑（FFmpeg 精确删除并合成）
- 🐛 Python 3.10 环境支持（解决兼容性问题）
- ⚙️ 可配置（自定义关键字列表和缓冲时间）
- 🎯 适用场景：YouTube 转播客、广告过滤、内容清理

**版本**: v1.1.0

[查看详情 →](./audiocut-keyword/)

---

### 🎙️ text-to-speech
文本转语音工具 - 支持播客脚本解析、情绪标记和后处理

**特点**：
- 🎤 高质量 TTS（基于 Microsoft Edge TTS，支持 18+ 种中文声音）
- 📝 脚本解析（自动识别并移除播客脚本中的注释和标记）
- 🎭 情绪标记（支持 SSML 情绪标记处理）
- 🎵 后处理集成（可选集成 voice-changer 进行变声）
- ⚙️ 高度可配置（所有功能都可通过配置文件控制）
- 🎯 适用场景：播客制作、有声读物、视频配音、教育培训

**版本**: v1.1.0

[查看详情 →](./text-to-speech/)

---

### 📹 video-downloader
下载 YouTube 视频，完全控制质量和格式设置

**特点**：
- 🎬 多种质量选项（最佳、1080p、720p、480p、360p）
- 🎵 纯音频下载为 MP3 格式
- 📦 多种格式支持（MP4、WebM、MKV）
- 🔄 自动安装依赖
- 📊 视频信息显示

**版本**: v1.1.0

[查看详情 →](./video-downloader/)

源自：https://github.com/ComposioHQ/awesome-claude-skills

---

### 🎨 image-generator
通用图片生成 Skill，支持多种 AI 模型（ModelScope、Gemini 等），可被其他 Skills 调用

**特点**：
- 🤖 支持多个 AI 模型（ModelScope、Gemini 等）
- 🎯 灵活的提示词和参数配置
- 📁 自动保存生成的图片
- 🔌 可被其他 Skills 调用的模块化设计
- ⚙️ 易于配置的模型切换

**版本**: v1.1.0

[查看详情 →](./image-generator/)

---

### 🔥 code-roaster
用 Gordon Ramsay 风格毒舌吐槽代码质量，生成搞笑且实用的代码审查报告

**特点**：
- 🎯 多维度分析（代码异味、Bug、安全、性能、最佳实践）
- 😂 Gordon Ramsay 风格的犀利吐槽
- 📊 详细的 Markdown 格式报告
- 🎚️ 三种模式（温和/标准/残暴）

**版本**: v1.1.0

[查看详情 →](./code-roaster/)

---

### 📹 youtube-to-blog-post
将 YouTube 视频转换为 SEO 优化的 Hexo 博客文章

**特点**：
- ✅ 智能内容提取 - 从视频描述提取真实内容和代码示例
- 🚀 SEO 优化 - 自动生成 160 字符描述、5-8 个高质量关键词
- 🎨 封面图 - 自动使用 YouTube 高清缩略图
- 🤖 AI 痕迹去除 - 内置自然语言处理，去除 AI 写作痕迹
- 📝 友好人性化 - 确保人性化后仍符合 SEO 标准
- 🌐 多格式支持 - 自动生成英文文件名（kebab-case）

**版本**: v3.1

[查看详情 →](./youtube-to-blog-post/)

---

### 📤 youtube-publisher
YouTube 视频发布工具 - 上传视频并自动设置封面和字幕

**特点**：
- 📤 视频上传 - 支持 MP4, MOV, AVI, WMV, FLV, 3GP, MPEG（最大 256GB）
- 🖼️ 封面图 - 支持本地路径或 URL
- 📝 字幕上传 - 支持 SRT/VTT 格式，自动设置语言
- 🏷️ 完整元数据 - 标题、描述、标签、分类
- 🔒 隐私设置 - public / unlisted / private
- 📋 播放列表 - 自动添加到指定播放列表
- ⚡ YouTube Short - 支持短视频标记
- 👁️ Dry-run 预览 - 不实际上传，预览设置

**版本**: v1.1.0

[查看详情 →](./youtube-publisher/)

---

### 📋 invoice-scanner
扫描目录识别所有类型发票（交通、住宿、餐饮等），提取关键信息并生成分类统计报告

**版本**: v2.5.0

[查看详情 →](./invoice-scanner/)

---

### 🐦 x-fetcher
抓取 X (Twitter) 推文和长文章，自动保存为 Markdown 格式

**特点**：
- 📝 抓取普通推文和 X Article 长文章
- 💾 自动保存为格式化的 Markdown 文件
- 🖼️ 媒体文件下载（图片/视频）
- 📊 获取互动数据（点赞、转发、浏览量、书签数）
- ⚙️ 灵活配置（项目级和用户级配置文件）
- 🔗 结构化存储（按用户名分类）
- 🎯 首次运行智能引导

**版本**: v1.1.0

**基于**: [Jane-xiaoer/x-fetcher](https://github.com/Jane-xiaoer/x-fetcher)

[查看详情 →](./x-fetcher-skill/)

---

## 🔧 安装使用

每个 skill 都是独立的，可以单独使用或组合使用。

### 基本用法

```bash
# 使用某个 skill
python3 ~/.claude/skills/<skill-name>/scripts/script.py [arguments]

# 或通过 Claude Code 调用
/<skill-name> [arguments]
```

### 依赖安装

每个 skill 可能有不同的依赖要求，请参考各 skill 的 README 文件。

### Skill 组合示例

```bash
# YouTube 下载 → 关键字过滤 → 变声 → 发布到小宇宙
youtube-to-xiaoyuzhou <url> --filter-keywords --change-voice female_3

# 文本转语音 → 变声
text-to-speech script.txt --voice female_3
```

---

## 📝 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
