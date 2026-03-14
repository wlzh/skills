# quark-mswnlz-publisher

**版本**: v1.0.0

夸克网盘 → mswnlz GitHub 资源仓库 → 站点自动更新，一条龙发布。

---

## 功能概述

| 功能 | 说明 |
|------|------|
| 夸克批量转存 | 新建批次文件夹 → 批量转存 URL 到夸克网盘 |
| 自动生成分享链接 | 永久有效期 + 加密链接 + 随机提取码 |
| 自动归类 | 根据 mswnlz 仓库 description 判断写入 book/movies 等仓库 |
| 自动落盘 | 追加/新建 `YYYYMM.md` + 更新 README 月份索引 |
| 自动提交 | commit（无链接，一条一行）+ push 到 GitHub |
| 强制触发站点构建 | `mswnlz.github.io` 站点构建（push 触发）并返回 Actions 链接/站点 URL |

---

## 环境要求

### 系统要求
- macOS / Linux
- Python 3.10+
- Git
- Chrome 浏览器（用于夸克登录）

### 目录结构（默认路径）

```
/Users/m./Documents/QNSZ/project/
├── QuarkPanTool/              # 夸克网盘自动化工具
│   ├── .venv/                 # Python 虚拟环境
│   ├── config/
│   │   ├── cookies.txt        # 夸克登录 Cookie（自动生成）
│   │   └── config.json        # 保存目录配置
│   ├── quark.py               # 核心库
│   ├── quark_login.py         # 登录脚本
│   └── ...
├── mswnlz/                    # mswnlz GitHub 仓库
│   ├── book/                  # 书籍资源仓库
│   ├── movies/                # 影视资源仓库
│   ├── mswnlz.github.io/      # 站点仓库
│   └── ...
└── skills/
    └── quark-mswnlz-publisher/  # 本 Skill
```

---

## 依赖安装

### 1. QuarkPanTool 环境配置

```bash
# 克隆 QuarkPanTool 仓库
cd /Users/m./Documents/QNSZ/project
git clone https://github.com/nichuanfang/QuarkPanTool.git
cd QuarkPanTool

# 创建虚拟环境
python3 -m venv .venv
. .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（用于登录）
playwright install chromium
```

**requirements.txt 内容**：
```
httpx
retrying==1.3.4
prettytable==3.10.0
playwright==1.43.0
tqdm>=4.66.3
colorama
```

### 2. GitHub SSH 配置

确保已配置 SSH 密钥并可访问 mswnlz 组织仓库：

```bash
# 测试 SSH 连接
ssh -T git@github.com

# 应该看到：
# Hi username! You've successfully authenticated...

# 如果未配置，请运行：
ssh-keygen -t ed25519 -C "your_email@example.com"
# 然后将 ~/.ssh/id_ed25519.pub 添加到 GitHub Settings → SSH Keys
```

### 3. GitHub Token（可选）

用于调用 GitHub API 获取仓库列表，**不强制要求**。

- 如果不配置：API 请求可能受速率限制（60 次/小时）
- 如果配置：速率限制提升至 5000 次/小时

**创建 Token 步骤**：
1. 访问 https://github.com/settings/tokens
2. Generate new token (classic)
3. 勾选 `public_repo` 权限
4. 生成并保存 Token

**使用方式**：
```bash
# 方式1：环境变量（推荐）
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"

# 方式2：运行时传入
GITHUB_TOKEN="ghp_xxxxxxxxxxxx" python scripts/mswnlz_publish.py --month 202603 --batch-json batch_share_results.json
```

⚠️ **安全提示**：不要在聊天中粘贴 Token，不要将 Token 写入任何文件！

---

## 夸克登录配置

### 首次登录

```bash
cd /Users/m./Documents/QNSZ/project/QuarkPanTool
. .venv/bin/activate
python quark_login.py
```

**登录流程**：
1. 脚本会自动打开 Chrome 浏览器
2. 在浏览器中扫描夸克网盘二维码登录
3. 登录成功后，Cookie 会自动保存到 `config/cookies.txt`
4. 看到 `登录成功！` 提示后关闭浏览器

### Cookie 有效期

- 夸克 Cookie 有效期约 **30 天**
- 过期后需要重新运行 `quark_login.py` 登录
- Cookie 文件位置：`QuarkPanTool/config/cookies.txt`

### 验证登录状态

```bash
# 检查 Cookie 文件是否存在
ls -la QuarkPanTool/config/cookies.txt

# 如果文件为空或不存在，需要重新登录
```

---

## 使用方法

### 完整流程

#### 步骤 1：准备输入文件

创建 `items.json`，格式如下：

```json
[
  {"title": "2025年杂志合集", "url": "https://pan.quark.cn/s/a95cc6d6cad1"},
  {"title": "大明王朝1566 最新修复4K版", "url": "https://pan.quark.cn/s/6a4aae85ac06"},
  {"title": "2026罗胖推荐的10本书", "url": "https://pan.quark.cn/s/5eb9a68e6236"}
]
```

**字段说明**：
- `title`（可选）：资源标题，用于归类和显示。如果不提供，会从分享链接提取
- `url`（必填）：夸克分享链接，格式 `https://pan.quark.cn/s/xxxxx`

#### 步骤 2：确保夸克登录状态

```bash
cd /Users/m./Documents/QNSZ/project/QuarkPanTool
. .venv/bin/activate

# 如果 Cookie 不存在或过期，运行登录
python quark_login.py
```

#### 步骤 3：批量转存 + 生成分享链接

```bash
python /Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/scripts/quark_batch_run.py \
  --label "短裤哥批次" \
  --month 202603 \
  --items-json items.json \
  --out-json batch_share_results.json
```

**参数说明**：
| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `--label` | 否 | 批次标签，用于文件夹命名 | `短裤哥批次` |
| `--month` | 否 | 目标月份 YYYYMM | 当前月份 |
| `--items-json` | 是 | 输入文件路径 | - |
| `--out-json` | 是 | 输出文件路径 | - |

**输出文件 `batch_share_results.json` 格式**：
```json
{
  "batch_folder_name": "2026-03-14_1330_短裤哥批次",
  "batch_folder_fid": "abc123...",
  "items": [
    {"title": "2025年杂志合集", "input_url": "https://pan.quark.cn/s/xxx"}
  ],
  "share_results": [
    {
      "name": "2025年杂志合集",
      "fid": "def456...",
      "share_id": "xyz789",
      "share_url": "https://pan.quark.cn/s/abc123?pwd=K3M8"
    }
  ]
}
```

#### 步骤 4：发布到 GitHub 仓库

```bash
python /Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/scripts/mswnlz_publish.py \
  --month 202603 \
  --batch-json batch_share_results.json
```

**参数说明**：
| 参数 | 必填 | 说明 |
|------|------|------|
| `--month` | 是 | 目标月份 YYYYMM |
| `--batch-json` | 是 | 步骤 3 生成的输出文件 |

**执行内容**：
1. 根据 GitHub API 获取 mswnlz 组织仓库列表
2. 根据标题关键词自动归类到对应仓库
3. 克隆/更新本地仓库（如果不存在）
4. 追加内容到 `YYYYMM.md`
5. 更新 `README.md` 月份索引
6. Git commit + push

#### 步骤 5：触发站点重建

```bash
bash /Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/scripts/trigger_site_rebuild.sh
```

**执行内容**：
1. 在 `mswnlz.github.io` 仓库创建空提交
2. Push 到 main 分支
3. 触发 GitHub Actions 构建流程

**查看构建状态**：
- Actions 页面：https://github.com/mswnlz/mswnlz.github.io/actions
- 构建时间：约 3-5 分钟

**站点地址**：
- 主站：https://doc.869hr.uk
- 书籍页：https://doc.869hr.uk/book/
- 影视页：https://doc.869hr.uk/movies/

---

## 归类规则

### 自动归类逻辑

脚本会根据资源标题中的关键词自动归类：

| 关键词 | 目标仓库 |
|--------|----------|
| 影视、电影、剧、纪录片、演唱会 | `movies` |
| 书、书单、新书、杂志、电子书、合集 | `book` |
| 课程、教程、学习 | `curriculum` |
| 工具、软件、插件 | `tools` |
| 健康、养生 | `healthy` |
| 自媒体、流量、变现 | `self-media` |
| 跨境、外贸、亚马逊 | `cross-border` |
| 教育、学而思、猿辅导 | `edu-knowlege` |
| AI、提示词、人工智能 | `AIknowledge` |

### 手动覆盖归类

如果自动归类不准确，可以在 `items.json` 中添加 `repo` 字段：

```json
[
  {"title": "某个资源", "url": "https://pan.quark.cn/s/xxx", "repo": "book"}
]
```

---

## 输出格式

### YYYYMM.md 格式

```markdown
- 2025年杂志合集-超过100T资料总站网站-doc.869hr.uk | https://pan.quark.cn/s/abc123?pwd=K3M8
- 大明王朝1566-超过100T资料总站网站-doc.869hr.uk | https://pan.quark.cn/s/def456?pwd=M2N9
- 2026罗胖推荐的10本书-超过100T资料总站网站-doc.869hr.uk | https://pan.quark.cn/s/ghi789?pwd=P4Q1
```

**格式说明**：
- 每行一条记录
- 格式：`- {标题}{站点后缀} | {分享链接}`
- 分享链接已包含提取码（`?pwd=xxxx`）

### README.md 月份索引格式

```markdown
# 书籍资料

[202603](202603.md) [202510](202510.md) [202509](202509.md) ...

这里是书籍资料相关的内容...
```

### Git Commit Message 格式

```
增加 2025年杂志合集
增加 大明王朝1566
增加 2026罗胖推荐的10本书
```

**规则**：
- 每条资源一行
- 不包含链接
- 使用中文

---

## 故障排除

### 问题 1：夸克登录失败

**症状**：`quark_login.py` 运行后提示登录失败

**解决方案**：
1. 确保已安装 Playwright 浏览器：`playwright install chromium`
2. 检查 Chrome 浏览器是否正常安装
3. 尝试手动登录夸克网盘后再运行脚本
4. 删除 `config/cookies.txt` 后重新登录

### 问题 2：Cookie 过期

**症状**：转存时提示 `未登录` 或 `登录已过期`

**解决方案**：
```bash
cd /Users/m./Documents/QNSZ/project/QuarkPanTool
rm config/cookies.txt
. .venv/bin/activate
python quark_login.py
```

### 问题 3：Git Push 失败

**症状**：`git push origin main` 报错

**解决方案**：
1. 检查 SSH 配置：`ssh -T git@github.com`
2. 确保有 mswnlz 组织仓库的写权限
3. 检查网络连接

### 问题 4：GitHub API 限流

**症状**：`rate limit exceeded`

**解决方案**：
```bash
# 设置 GitHub Token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

### 问题 5：站点未更新

**症状**：GitHub Actions 运行成功但站点内容未更新

**解决方案**：
1. 清除浏览器缓存
2. 检查 Actions 构建日志是否有错误
3. 等待 1-2 分钟让 CDN 缓存刷新

---

## 安全注意事项

### Token 安全
- ⚠️ **绝对不要**在聊天、代码、文档中粘贴 GitHub Token
- ⚠️ **绝对不要**将 Token 提交到 Git 仓库
- ✅ 使用环境变量传递 Token
- ✅ Token 只需要 `public_repo` 权限即可

### Cookie 安全
- 夸克 Cookie 存储在本地 `config/cookies.txt`
- 不要将此文件提交到 Git（已在 `.gitignore` 中）
- Cookie 包含你的登录凭证，不要分享给他人

### SSH 密钥安全
- 私钥（`~/.ssh/id_ed25519`）不要分享
- 只将公钥（`~/.ssh/id_ed25519.pub`）添加到 GitHub

---

## 文件清单

```
quark-mswnlz-publisher/
├── SKILL.md                              # Skill 定义文件
├── README.md                             # 本文档
├── references/
│   └── mswnlz-repos-cache.json           # mswnlz 仓库描述缓存
└── scripts/
    ├── quark_batch_run.py                # 夸克批量转存脚本
    ├── mswnlz_publish.py                 # GitHub 发布脚本
    └── trigger_site_rebuild.sh           # 站点重建触发脚本
```

---

## 更新日志

### v1.0.0 (2026-03-14)
- 初始版本
- 支持夸克批量转存 + 生成分享链接
- 支持自动归类到 mswnlz 仓库
- 支持自动更新 YYYYMM.md 和 README.md
- 支持触发站点重建

---

## 相关链接

- 夸克网盘：https://pan.quark.cn
- QuarkPanTool：https://github.com/nichuanfang/QuarkPanTool
- mswnlz 组织：https://github.com/mswnlz
- 站点地址：https://doc.869hr.uk
- Skills 仓库：https://github.com/wlzh/skills
