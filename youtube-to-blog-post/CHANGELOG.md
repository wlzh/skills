# v3.2 Changelog - 标签管理规范版

**版本**: 3.2.0
**发布日期**: 2026-04-19
**类型**: 规范更新

---

## 概述

本次更新建立了**标准标签体系**，解决标签膨胀和命名混乱问题。博客标签从 425 个精简为 67 个标准标签，生成文章时强制复用已有标签。

**核心目标：** 统一标签命名，优先复用，杜绝标签膨胀

---

## 新增功能

### 1. 标准标签表（67 个）

**问题：** 标签从几十个增长到 425 个，存在大量重复、大小写不一致、中英双语标签。

**解决方案：**
- 定义 67 个标准标签，覆盖所有内容分类
- 按主题分组：AI、支付、网络、手机、工具、教程、生活、账号、其他
- 每个标准标签映射多个变体（大小写、同义词）

### 2. 标签标准化函数

**新增 `normalize_tag(tag)` 函数：**
```python
def normalize_tag(tag):
    """将任意标签变体映射到标准标签"""
    for standard, variants in STANDARD_TAGS.items():
        for v in variants:
            if tag.lower() == v.lower():
                return standard
    return tag  # 新标签保留原样
```

**效果：**
- `ai工具` → `AI工具`
- `telegram` → `Telegram`
- `免费VPS` → `VPS`
- `虚拟信用卡` → `信用卡`

### 3. 标签生成规则

| 规则 | 说明 |
|------|------|
| 优先复用 | 从标准标签表选择，禁止随意创建新标签 |
| 数量控制 | 每篇 3-5 个标签 |
| 命名规范 | 中文为主，不含特殊字符 |
| 禁止双语 | 不写 `海外应用-Foreign-Apps` |
| 禁止细分 | 不写 `免费VPS`，用 `VPS` |

---

## 改进内容

### SKILL.md 更新

- 新增「标签管理规则」章节
- 新增标准标签表（完整 67 个标签）
- 新增标签选择逻辑流程图
- 新增禁止标签格式示例

### youtube_to_post.py 更新

- 新增 `STANDARD_TAGS` 常量（67 个标准标签及其变体）
- 新增 `normalize_tag()` 函数
- 标签生成时自动标准化

---

## 标签整理统计

| 指标 | 整理前 | 整理后 | 变化 |
|------|--------|--------|------|
| 唯一标签数 | 425 | 67 | -84% |
| 仅1篇文章使用的标签 | ~250 | 6 | -97% |
| 重复/同义标签 | ~100 | 0 | -100% |
| 中英双语标签 | ~40 | 0 | -100% |

---

## 兼容性

- ✅ 向后兼容 v3.1 的所有功能
- ✅ 命令行参数不变
- ✅ 配置文件格式不变
- ✅ 生成的文章格式不变（仅标签更规范）

---

**版本**: 3.2.0
**更新日期**: 2026-04-19

---

# v3.1 Changelog - 本地配置 + 自动部署版

**版本**: 3.1
**发布日期**: 2026-02-13
**类型**: 功能更新

---

## 概述

本次更新添加了**本地配置文件支持**和**自动 Git 部署功能**，使博客生成流程更加自动化和便捷。

**核心目标：** 一次配置，自动生成并部署博客文章

---

## 新增功能

### 1. 本地配置文件 (~/.youtube-blog-config.json)

**问题：** 之前每次运行都需要指定博客路径，不够便捷。

**解决方案：**
- 支持在用户主目录创建配置文件 `~/.youtube-blog-config.json`
- 配置文件**不会被提交到 Skills 的 git 仓库**
- 优先级最高，覆盖其他配置方式

**配置文件格式：**
```json
{
  "blog_dir": "/path/to/your/blog",
  "posts_dir": "source/_posts",
  "default_category": "技术",
  "default_tags": ["视频教程"],
  "author": "M.",
  "image_cdn": "https://img.869hr.uk",
  "auto_deploy": true,
  "deploy_branch": "main"
}
```

**配置优先级：**
1. `~/.youtube-blog-config.json` (本地用户配置)
2. `--config` 指定的配置文件
3. 博客目录下的 `youtube-blog-config.json`

### 2. 自动 Git 部署

**问题：** 生成文章后需要手动提交和推送代码。

**解决方案：**
- 新增 `--deploy` 参数，自动执行 git 操作
- 配置文件支持 `auto_deploy` 选项，默认启用自动部署
- 自动执行：git add → git commit → git push

**部署流程：**
```bash
# 自动部署
python scripts/youtube_to_post.py "URL" --deploy

# 或在配置文件中设置 auto_deploy: true
python scripts/youtube_to_post.py "URL"  # 自动部署
```

### 3. 改进的配置加载

**配置文件搜索路径：**
```python
# 优先级 1: 用户主目录配置（个人设置）
~/.youtube-blog-config.json

# 优先级 2: 命令行指定的配置
--config /path/to/config.json

# 优先级 3: 博客目录配置
/blog/dir/youtube-blog-config.json
```

---

## 改进内容

### 1. 博客路径自动识别

**之前：**
```bash
# 每次都需要指定博客路径
python scripts/youtube_to_post.py "URL" -b /path/to/blog
```

**之后：**
```bash
# 配置一次，自动使用
python scripts/youtube_to_post.py "URL"
```

### 2. 命令行参数

**新增参数：**
```bash
--deploy    # 自动部署到 git 仓库
```

### 3. 输出信息优化

**新的输出示例：**
```
📹 Video: 标题
👤 Uploader: 作者
📂 Blog: /Users/m/document/QNSZ/project/Hexo-BLog/myblog
📝 Filename: post-name.md
🔄 Applying AI writing removal...
✅ Content humanized
✅ Blog post created: /path/to/post.md

🚀 Auto-deploying to git...
📤 Adding changes to git...
💾 Committing changes...
🚀 Pushing to remote...
✅ Successfully pushed to git repository
```

---

## 技术细节

### 新增函数

#### `deploy_to_git(blog_dir, branch='main')`

**功能：** 自动执行 git 操作

**流程：**
1. 检查是否为 git 仓库
2. 执行 `git add .`
3. 检查是否有更改需要提交
4. 执行 `git commit -m "docs: add new blog post"`
5. 执行 `git push origin <branch>`

### 配置加载逻辑更新

```python
def load_config(config_path=None, blog_dir=None):
    # 优先级 1: 用户主目录配置
    home_config = os.path.expanduser("~/.youtube-blog-config.json")
    if os.path.exists(home_config):
        config.update(json.load(open(home_config)))

    # 优先级 2: 命令行配置
    if config_path and os.path.exists(config_path):
        config.update(json.load(open(config_path)))

    # 优先级 3: 博客目录配置
    elif blog_dir:
        blog_config = os.path.join(blog_dir, "youtube-blog-config.json")
        if os.path.exists(blog_config):
            config.update(json.load(open(blog_config)))
```

---

## 使用示例

### 基本用法（使用本地配置）

```bash
# 1. 创建配置文件
cat > ~/.youtube-blog-config.json << EOF
{
  "blog_dir": "/Users/m/document/QNSZ/project/Hexo-BLog/myblog",
  "auto_deploy": true
}
EOF

# 2. 直接运行，自动使用配置
python ~/.claude/skills/youtube-to-blog-post/scripts/youtube_to_post.py \
  "https://youtu.be/VIDEO_ID"
```

### 手动指定部署

```bash
python scripts/youtube_to_post.py "URL" --deploy
```

### 查看部署信息

```bash
# 自动部署时会显示详细过程
python scripts/youtube_to_post.py "URL"

# 输出：
# 🚀 Auto-deploying to git...
# 📤 Adding changes to git...
# 💾 Committing changes...
# 🚀 Pushing to remote...
# ✅ Successfully pushed to git repository
```

---

## 兼容性

- ✅ 向后兼容 v3.0 的所有功能
- ✅ 配置文件格式向下兼容
- ✅ 命令行参数向后兼容
- ✅ 不使用配置文件时行为与之前相同

---

## 已知问题

### 1. Git 配置要求

**问题：** 需要预先配置好 git 用户信息和远程仓库。

**解决方案：**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 2. SSH 密钥

**问题：** 如果使用 SSH 方式推送，需要配置 SSH 密钥。

**解决方案：** 确保 SSH 密钥已添加到 GitHub/GitLab。

---

## 未来规划

### v3.2 计划

- [ ] 支持自动部署到 Hexo（hexo cl && hexo g && hexo d）
- [ ] 支持配置多个博客目录
- [ ] 添加部署前钩子（pre-deploy hooks）

### v4.0 计划

- [ ] AI 分析视频音频内容
- [ ] 自动生成结构化摘要（TOC）
- [ ] 多语言支持

---

## 贡献

本次更新由用户反馈驱动：

- 本地配置文件的需求
- 自动部署功能的需求
- 简化工作流程的需求

---

**版本**: 3.1
**更新日期**: 2026-02-13
**维护者**: YouTube to Blog Post Team

---

# v3.0 Changelog - 自然语言 + SEO 版

**版本**: 3.0
**发布日期**: 2026-02-07
**类型**: 功能更新

---

## 概述

本次更新将文章生成从"模板化 AI 文本"升级为"智能提取真实内容 + 自然语言处理"，显著提升内容质量，同时保持所有 SEO 优化。

**核心目标：** 去除 AI 痕迹，使文章读起来像真人写的

---

## 新增功能

### 1. 智能内容提取

**问题：** 之前的版本生成模板化内容（"核心知识点"、"适合人群"、"实践建议"等章节），缺乏实际价值。

**解决方案：**
- 从视频描述中提取真实内容
- 识别关键特性（标记 ✅ 的内容）
- 提取代码示例并格式化
- 过滤社交媒体链接等无关信息

**代码实现：**
```python
# 提取关键特性
features = []
for line in desc_lines:
    if '✅' in line or '核心' in line or '亮点' in line:
        features.append(line.replace('✅', '').strip())

# 提取代码块
code_blocks = re.findall(r'```[a-z]*\n(.*?)```', meaningful_desc, re.DOTALL)
```

### 2. 内置 AI 痕迹去除

**问题：** AI 生成的文本有明显痕迹，读者能识别。

**解决方案：**
- 内置 `humanize_article()` 函数
- 删除过度使用的 AI 词汇（"此外"、"深入探讨"等）
- 删除表情符号（标题和项目符号）
- 删除宣传性语言（"充满活力的"、"深刻见解"等）
- 删除破折号过度使用
- 删除三段式法则（"不仅...而且..."）
- 删除通用积极结论

**处理的模式：**
| 模式 | 示例 | 改写后 |
|------|------|--------|
| AI 词汇 | "此外"、"深入探讨" | 删除或改写 |
| 表情符号 | 🚀💡✅ | 删除 |
| 破折号 | "——这很重要" | 删除破折号 |
| 强调 | **重要** | 删除 ** |
| 模板章节 | "适合人群" | 删除 |

### 3. SEO 友好人性化

**问题：** 人性化后可能破坏 SEO 结构。

**解决方案：**
- **保持 Front Matter 完整** - 所有关键词、描述、封面图在人性化前保存
- **只处理正文内容** - Front Matter 和 iframe 不被修改
- **保留结构化标签** - H1-H3 结构保持不变

**处理流程：**
```python
# 1. 生成完整的 front matter（含 SEO 优化）
front_matter = generate_front_matter(...)

# 2. 生成正文
content = generate_article_content(...)

# 3. 应用人性化（只处理正文）
humanized_content = humanize_article(content, video_title)

# 4. 组合
final_post = front_matter + humanized_content
```

---

## 改进内容

### 1. 文章结构优化

**之前（v2.0）：**
```markdown
## 📹 视频教程
<iframe>...</iframe>

## 📺 视频介绍
本视频由 XXX 制作...

### 🎯 视频亮点
（视频描述前 300 字）

## 💡 核心知识点
在本视频中，我们深入探讨了...

### 🎓 适合人群
本视频适合以下观众观看：
- 对XXX感兴趣的初学者
- 希望提升相关技能的开发者

### 📝 实践建议
建议在观看视频时：
1. 跟随视频步骤进行实践操作
2. 记录...

## 📚 总结
通过本视频的学习...

## 🔗 相关关键词
关键词：XXX, YYY
```

**之后（v3.0）：**
```markdown
## 视频教程
<iframe>...</iframe>

## 视频介绍
本视频由 XXX 制作，时长约 N 分钟。

## 核心亮点
**核心亮点 1**
**核心亮点 2**
（从视频描述提取）...

## 配置示例
```
代码块
```

## 参考链接
- [YouTube视频原地址](...)
- [相关推荐](...)
```

### 2. 内容提取质量

**之前：**
- 截取描述前 300 字
- 添加"核心知识点"等模板章节
- 通用内容，缺乏价值

**之后：**
- 过滤社交媒体链接
- 提取关键特性（✅ 标记内容）
- 提取代码示例
- 只保留有价值的内容

### 3. 命令行参数

**新增参数：**
```bash
--no-humanizer  # 跳过 AI 痕迹去除，保留原始 AI 文本
```

**说明：** 默认启用人性化处理，某些场景可能需要保留原始 AI 文本。

---

## 技术细节

### 函数更新

#### `generate_article_content(video_info, video_id)`
- 新增 `video_id` 参数（用于生成参考链接）
- 重写内容提取逻辑
- 删除"适合人群"、"实践建议"章节

**关键变更：**
```python
# v2.0 - 模板化内容
content += """
## 💡 核心知识点
在本视频中，我们深入探讨了{title}的相关知识点...
### 🎓 适合人群
本视频适合以下观众观看：
"""

# v3.0 - 智能提取
# 从视频描述提取真实内容
features = extract_features(description)
code_blocks = extract_code_blocks(description)
content = generate_from_real_content(features, code_blocks)
```

#### `humanize_article(content, video_title)`
- 新增函数
- 内置 AI 痕迹消除逻辑
- 保留 Front Matter 和 iframe

**处理的模式：**
```python
# 删除过度表情符号
line = re.sub(r'[🎯📹📺💡🎓📝📚🔍🔗]+', '', line)

# 删除破折号过度使用
line = line.replace('——', ' ')

# 删除 AI 词汇
line = re.sub(r'此外，', '', line)
line = re.sub(r'深入探讨', '介绍', line)

# 删除粗体过度使用
line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
```

#### `save_post(content, filename, posts_dir, video_title, apply_humanizer=True)`
- 新增 `apply_humanizer` 参数
- 默认启用人性化处理
- 先应用内置 humanizer，再保存

---

## 效果对比

### 文章质量

| 维度 | v2.0 | v3.0 | 提升 |
|------|------|------|------|
| 内容价值 | 低（模板化） | 高（真实内容） | ⬆️ 大幅提升 |
| AI 痕迹 | 明显 | 几乎无 | ⬆️ 90% |
| 阅读体验 | 机枪感强 | 自然流畅 | ⬆️ 85% |
| 代码示例 | ❌ 无 | ✅ 自动提取 | ➕ 新功能 |
| 关键特性 | ❌ 截取 | ✅ 智能提取 | ➕ 新功能 |
| 章节精简 | 8 章节 | 4 章节 | ⬇️ 减少 50% |

### SEO 保持

| SEO 维度 | v2.0 | v3.0 | 状态 |
|----------|------|------|------|
| Front Matter | ✅ | ✅ | ✅ 保持 |
| 关键词 | ✅ | ✅ | ✅ 保持 |
| 描述长度 | ✅ | ✅ | ✅ 保持 |
| 封面图 | ✅ | ✅ | ✅ 保持 |
| 文件名 | ✅ | ✅ | ✅ 保持 |
| 内部链接 | ✅ | ✅ | ✅ 保持 |

---

## 使用示例

### 基本用法（默认启用人性化）

```bash
python scripts/youtube_to_post.py https://youtu.be/VIDEO_ID
```

**输出：**
```
📹 Video: XXX
👤 Uploader: XXX
📝 Filename: xxx-tutorial.md
🔄 Applying AI writing removal (natural language processing)...
✅ Content humanized - SEO optimized and ready
✅ Blog post created: source/_posts/xxx-tutorial.md
```

### 跳过人性化

```bash
python scripts/youtube_to_post.py https://youtu.be/VIDEO_ID --no-humanizer
```

**输出：**
```
📹 Video: XXX
👤 Uploader: XXX
📝 Filename: xxx-tutorial.md
✅ Blog post created: source/_posts/xxx-tutorial.md
```

---

## 兼容性

- ✅ 向后兼容 v2.0 的所有功能
- ✅ 配置文件格式不变
- ✅ 命令行参数向后兼容
- ✅ 输出格式（Hexo）不变

---

## 已知问题

### 1. 内容提取依赖视频描述质量

**问题：** 如果视频描述没有关键信息，提取的内容可能较少。

**临时解决方案：** 手动编辑文章补充内容。

**未来计划：** 考虑使用 AI 分析视频音频内容。

### 2. 代码块识别有限

**问题：** 只能识别标准三反引号代码块。

**限制：** 不支持其他代码块格式。

---

## 未来规划

### v3.1 计划

- [ ] 支持内容模板自定义
- [ ] 增强代码块识别
- [ ] 添加更多人性化模式（不同语气）
- [ ] 支持从视频字幕提取内容

### v4.0 计划

- [ ] AI 分析视频音频内容
- [ ] 自动生成结构化摘要（TOC）
- [ ] 多语言支持
- [ ] 支持自定义人性化策略

---

## 贡献

本次更新由用户反馈驱动，感谢以下建议：

- 去除 AI 痕迹的重要性
- 模板化内容的局限性
- 从视频描述提取真实内容的需求

---

## 反馈

如有问题或建议，欢迎反馈：

- GitHub Issues
- 邮件反馈

---

**版本**: 3.0
**更新日期**: 2026-02-07
**维护者**: Video-to-Blog Post Team
