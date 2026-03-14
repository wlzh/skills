# quark-mswnlz-publisher

**版本**: v1.3.0

夸克网盘 → mswnlz GitHub 资源仓库 → 站点自动更新，一条龙发布。

---

## 📺 视频教程

**【资源运营神器 Skills】完全开源，夸克网盘 + GitHub 一条龙全自动发布工具 (v1.2.0)！**

👉 [YouTube 视频教程](https://youtu.be/s1RhLDOGOfQ)

内容包括：
- 转存夸克资源到网盘
- 自动生成加密分享链接
- 智能归类到 GitHub 仓库
- Telegram 自动通知
- 站点自动更新

## 📝 文字教程

👉 [Twitter/X 文字教程](https://x.com/gxjdian/status/2032766709711712491)

---

## 功能概述

| 功能 | 说明 |
|------|------|
| 夸克批量转存 | 新建批次文件夹 → 批量转存 URL 到夸克网盘 |
| 推广文件复制 | 从模板文件夹复制推广文件到**每个资源文件夹内部** |
| 自动生成分享链接 | 永久有效期 + 加密链接 + 随机提取码 |
| 自动归类 | 根据 mswnlz 仓库 description 判断写入 book/movies 等仓库 |
| 自动落盘 | 追加/新建 `YYYYMM.md` + 更新 README 月份索引 |
| 自动提交 | commit（无链接，一条一行）+ push 到 GitHub |
| Telegram 通知 | 频道单条 + 群组汇总通知 |
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
        ├── scripts/
        │   ├── quark_batch_run.py
        │   ├── quark_copy.py       # 推广文件复制
        │   ├── mswnlz_publish.py   # GitHub 发布 + Telegram 通知
        │   └── trigger_site_rebuild.sh
        └── promo_files/             # 推广文件本地备份
```

---

## 推广文件机制 🆕

### 工作原理

1. **准备阶段**：用户提前在夸克网盘创建 `temp/要共享的文件` 文件夹，上传推广文件
2. **执行阶段**：Skills 脚本从模板文件夹复制推广文件到每个分享文件夹

### 推广文件模板

夸克网盘路径：`temp/要共享的文件`

| 文件名 | 用途 |
|--------|------|
| `必看免责声明-及加入资源分享群 及 副业 0 成本赚钱教程-资源网站doc.869hr.uk.txt` | 免责声明 + 联系方式 + 赚钱教程 |
| `1.【解压密码869hr.uk】-移动端双击这里-资源网站doc.869hr.uk.html` | 移动端解压密码获取页面 |
| `0.【双击获取解压密码】-Mac系统双击这里-资源网站doc.869hr.uk.webloc` | Mac 快捷方式 |
| `0.【双击获取解压密码】-windows系统双击这里-资源网站doc.869hr.uk.url` | Windows 快捷方式 |
| `【！！！注意】一定要保存到自己的盘，防止失效！！！-资源网站doc.869hr.uk` | 保存提醒 |

### 本地备份

`promo_files/` 目录保存了推广文件的本地备份，用于参考和恢复。

---

## Telegram 通知机制 🆕

### 频道通知（@dabaziyuan）
- **每条资源单独发送**
- 包含：资源名称 + 资料站链接 + GitHub 链接
- 由 GitHub Workflow 自动触发

### 群组通知（tgmShare 话题5、tgmShareAI 话题2）
- **批量更新只发一条汇总消息**
- 包含：已更新仓库列表 + 资源数量 + 频道链接
- 由 Skills 脚本统一发送，避免刷屏

### 示例消息

**频道消息**：
```
📦 新增资源推送

增加 2026.3.3小说合集推荐

🔗 资料总站：https://doc.869hr.uk
📂 GitHub：https://github.com/mswnlz/book/commit/xxx
```

**群组汇总消息**：
```
📝 资源更新

已更新仓库：book、movies
共 3 项资源

📦 https://t.me/dabaziyuan
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

### 2. GitHub SSH 配置

确保已配置 SSH 密钥并可访问 mswnlz 组织仓库：

```bash
# 测试 SSH 连接
ssh -T git@github.com

# 应该看到：
# Hi username! You've successfully authenticated...
```

### 3. 准备推广文件模板

在夸克网盘中创建文件夹并上传推广文件：
1. 创建 `temp/要共享的文件` 文件夹
2. 上传推广文件（参见上方文件清单）

---

## 环境变量配置 ⚠️

在运行脚本前，需要设置以下环境变量：

```bash
# Telegram Bot Token（必须，用于发送通知）
export TELEGRAM_BOT_TOKEN="你的Bot Token"

# Telegram 群组配置（可选）
export TG_GROUP_1_ID="-1002573762160"
export TG_GROUP_1_THREAD="5"
export TG_GROUP_2_ID="-1003365897434"
export TG_GROUP_2_THREAD="2"

# Telegram 频道 ID（可选）
export TELEGRAM_CHANNEL_ID="@dabaziyuan"

# GitHub Token（可选，用于 API 调用）
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

⚠️ **安全提示**：
- 永远不要将 Token 硬编码在脚本中
- 永远不要将 Token 提交到 Git 仓库

---

## 使用方法

### 完整流程

#### 步骤 1：准备输入文件

创建 `items.json`：

```json
[
  {"title": "2025年杂志合集", "url": "https://pan.quark.cn/s/a95cc6d6cad1"},
  {"title": "大明王朝1566 4K版", "url": "https://pan.quark.cn/s/6a4aae85ac06"}
]
```

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

#### 步骤 4：复制推广文件 🆕

```bash
python /Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/scripts/quark_copy.py \
  --batch-json batch_share_results.json
```

#### 步骤 5：发布到 GitHub + 发送 Telegram 通知

```bash
python /Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/scripts/mswnlz_publish.py \
  --month 202603 \
  --batch-json batch_share_results.json
```

#### 步骤 6：触发站点重建

```bash
bash /Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/scripts/trigger_site_rebuild.sh
```

---

## 归类规则

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

---

## 输出格式

### YYYYMM.md 格式

```markdown
- 2025年杂志合集-超过100T资料总站网站-doc.869hr.uk | https://pan.quark.cn/s/abc123?pwd=K3M8
- 大明王朝1566-超过100T资料总站网站-doc.869hr.uk | https://pan.quark.cn/s/def456?pwd=M2N9
```

### Git Commit Message 格式

```
增加 2025年杂志合集
增加 大明王朝1566
```

---

## 文件清单

```
quark-mswnlz-publisher/
├── SKILL.md                              # Skill 定义文件 (v1.2.0)
├── README.md                             # 本文档
├── references/
│   └── mswnlz-repos-cache.json           # mswnlz 仓库描述缓存
├── scripts/
│   ├── quark_batch_run.py                # 夸克批量转存脚本
│   ├── quark_copy.py                     # 推广文件复制脚本 🆕
│   ├── mswnlz_publish.py                 # GitHub 发布 + Telegram 通知
│   └── trigger_site_rebuild.sh           # 站点重建触发脚本
└── promo_files/                          # 推广文件本地备份 🆕
    ├── 必看免责声明-...txt
    ├── 1.【解压密码...】.html
    ├── 0.【双击获取...Mac】.webloc
    └── 0.【双击获取...Windows】.url
```

---

## 更新日志

### v1.3.0 (2026-03-14)
- 修复：推广文件复制到每个资源文件夹**内部**（而不是批次文件夹）
- 新增：视频教程和文字教程链接
- 新增：`copy_promo_to_folders.py` 脚本

### v1.2.0 (2026-03-14)
- 新增：推广文件复制功能（从模板文件夹复制）
- 新增：Telegram 群组汇总通知（多仓库只发一条）
- 优化：简化推广文件机制，不需要上传 API
- 更新：SKILL.md 和 README.md 文档

### v1.1.0 (2026-03-14)
- 新增：推广文件上传功能
- 新增：Telegram 群组汇总通知

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
- Telegram 频道：https://t.me/dabaziyuan
