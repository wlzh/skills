# quark-mswnlz-publisher

**版本**: v2.1.1

夸克网盘 + 百度网盘 → mswnlz GitHub 资源仓库 → 站点自动更新，一条龙发布。

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
│   │   ├── cookies.txt        # 夸克登录 Cookie（自动生成，由轮换器维护）
│   │   ├── cookies_1.txt      # 账号 1 Cookie（备份）
│   │   ├── cookies_2.txt      # 账号 2 Cookie（备份）
│   │   ├── account_state.json # 多账号轮换状态
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
        │   ├── quark_account_rotator.py  # 🆕 v2.1.0 多账号轮换
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

### 群组通知（tgmShare 话题5、tgmShareAI 话题2、tgmkno）
- **批量更新只发一条汇总消息**
- 格式与频道风格对齐：📦 新增资源推送 + 资源名称 + 更新仓库 + 查看详情 + 资料总站 + 资料频道
- 由 Skills 脚本统一发送，避免刷屏

### 示例消息

**频道消息**：
```
📦 新增资源推送

增加 2026.3.3小说合集推荐

🔗 查看详情：https://doc.869hr.uk/book/202603
🌐 资料总站：https://doc.869hr.uk
📦 资料频道：https://t.me/dabaziyuan
```

**群组汇总消息**：
```
📦 新增资源推送

增加 2026.3.3小说合集推荐
🔗 夸克链接：https://pan.quark.cn/s/xxx?pwd=xxx

已更新仓库：book

🔗 查看详情：https://doc.869hr.uk/book/202603
🌐 资料总站：https://doc.869hr.uk
📦 资料频道：https://t.me/dabaziyuan
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
export TG_GROUP_1_ID="-100XXXXXXXXXX"
export TG_GROUP_1_THREAD="5"
export TG_GROUP_2_ID="-100YYYYYYYYYY"
export TG_GROUP_2_THREAD="2"
export TG_GROUP_3_ID="@tgmkno"
export TG_GROUP_3_THREAD=""

# Telegram 频道 ID（可选）
export TELEGRAM_CHANNEL_ID="@your_channel"

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

## 归类规则（v1.4.4）

三层智能分类策略，优先级从高到低：

### 第一关：视频/影视类
命中以下任意关键词 → 直接归 `movies`

| 类别 | 关键词 |
|------|--------|
| 分辨率标识 | `4K`、`超清`、`蓝光`、`高清`、`1080P`、`2160P`、`720P` |
| 影视短语 | `电影`、`纪录片`、`演唱會`、`电视剧`、`剧集`、`连续剧` |
| 集数标识 | `全X集`、`第X集`、`X集全`、`X集完结` |
| 视频后缀 | `.mp4`、`.mkv`、`.avi`、`.rmvb`、`.mov` |

### 第二关：书籍类
能明确判断为书籍时 → 归 `book`

| 类别 | 关键词 |
|------|--------|
| 书类标识 | `书`（末尾）、`书单`、`新书`、`电子书`、`杂志` |
| 册/本标识 | `X册`、`X本`、`册全书`、`全集书` |

> 注意：v1.4.4 取消了"合集"关键词直接归 book 的规则，避免影视合集（如"BBC纪录片合集"）误归。

### 第三关：回退评分
名称和标题均无法明确判断时，遍历所有 mswnlz 仓库的 GitHub description，按关键词打分匹配：

| 仓库 | 描述关键词 |
|------|-----------|
| `book` | 书 |
| `movies` | 影视 |
| `curriculum` | 课程 |
| `tools` | 工具 |
| `healthy` | 健康 |
| `self-media` | 自媒体 |
| `cross-border` | 跨境 |
| `edu-knowlege` | 教育 |
| `AIknowledge` | AI |

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
├── SKILL.md                              # Skill 定义文件 (v2.0.0)
├── README.md                             # 本文档
├── references/
│   └── mswnlz-repos-cache.json           # mswnlz 仓库描述缓存
├── scripts/
│   ├── quark_batch_run.py                # 夸克批量转存脚本
│   ├── copy_promo_to_folders.py          # 推广文件复制脚本 🆕
│   ├── cleanup_junk_files.py             # 垃圾文件清理脚本 🆕 v2.0.0
│   ├── mswnlz_publish.py                 # GitHub 发布 + Telegram 通知
│   ├── pipeline_orchestrator.py          # 统一编排器 (v1.5.0+)
│   ├── trigger_site_rebuild.sh           # 站点重建触发脚本
│   └── config/
│       └── junk_files.json               # 垃圾文件名配置 🆕 v2.0.0
└── promo_files/                          # 推广文件本地备份 🆕
    ├── 必看免责声明-...txt
    ├── 1.【解压密码...】.html
    ├── 0.【双击获取...Mac】.webloc
    └── 0.【双击获取...Windows】.url
```

---

## 多账号轮换 🆕 v2.1.0

支持多个夸克账号按批次自动轮换，分摊转存压力，避免单账号被限速。

### 工作原理（方案B：按批次轮换 + 做法甲：cookie 文件复制）

- 每次执行 `quark_batch_run.py` 时，自动轮换到下一个账号
- 轮换逻辑：将下一个账号的 cookie 文件复制为 `cookies.txt`，`quark.py` 零改动
- 状态记录在 `config/account_state.json`，自动维护

### 配置方法

1. **登录每个账号**，获取完整 cookie：
```bash
cd QuarkPanTool
. .venv/bin/activate
python quark_login.py  # 登录账号1
# 登录后：cp config/cookies.txt config/cookies_1.txt

python quark_login.py  # 登录账号2
# 登录后：cp config/cookies.txt config/cookies_2.txt
```

2. **添加更多账号**（可选）：
- 保存 `cookies_3.txt`、`cookies_4.txt`... 即可，轮换器自动扫描发现

3. **无需其他配置**，`quark_batch_run.py` 执行时自动轮换

### 使用方式

```bash
# 正常使用（自动轮换到下一个账号）
python quark_batch_run.py --label "短裤哥批次" ...

# 强制指定账号（某账号被限速时临时使用）
python quark_batch_run.py --force-account 1 ...

# 跳过轮换（使用当前 cookies.txt）
python quark_batch_run.py --no-rotate ...
```

### 管理命令

```bash
# 查看轮换状态
cd QuarkPanTool
. .venv/bin/activate
python scripts/quark_account_rotator.py --config-dir ./config status

# 手动轮换到下一个
python scripts/quark_account_rotator.py --config-dir ./config next

# 列出所有账号
python scripts/quark_account_rotator.py --config-dir ./config list

# 强制切换到指定账号
python scripts/quark_account_rotator.py --config-dir ./config force 2
```

### 文件说明

| 文件 | 说明 |
|------|------|
| `config/cookies_1.txt` | 账号1 cookie |
| `config/cookies_2.txt` | 账号2 cookie |
| `config/cookies.txt` | 当前激活的 cookie（由轮换器维护） |
| `config/cookies.txt.bak` | 切换前的备份 |
| `config/account_state.json` | 轮换状态（当前账号、历史记录） |

---

## 更新日志

### v2.1.1 (2026-07-19)
- 🔧 **copy_promo 动态发现推广文件夹**：不再硬编码账号1的 fid，改为先试硬编码 → 失败则在 `temp/` 下按名称查找，自动适配多账号场景

### v2.1.0 (2026-07-19)
- 🆕 **多账号轮换**：支持多个夸克账号按批次自动轮换，分摊转存压力
  - 新增 `scripts/quark_account_rotator.py` 独立轮换器
  - `quark_batch_run.py` 集成轮换逻辑，支持 `--force-account` 和 `--no-rotate` 参数
  - 采用方案B（按批次轮换）+ 做法甲（cookie 文件复制），对现有代码零侵入
  - 状态记录在 `config/account_state.json`，支持任意数量的账号
  - 输出 JSON 新增 `quark_account` 字段，标记本批次使用的账号

### v2.0.0 (2026-07-15)
- 🆕 **垃圾文件清理模块**：转存后自动删除原分享者植入的推广/广告文件
  - 新增 `scripts/cleanup_junk_files.py` 独立清理脚本，支持夸克/百度/阿里云三端
  - 新增 `config/junk_files.json` 垃圾文件名配置文件（子串匹配，可随时追加）
  - `pipeline_orchestrator.py` 在 A 段与 B 段之间插入 cleanup 步骤
  - QuarkPanTool `quark.py` 新增 `delete_files(fid_list)` API
  - QuarkPanTool `aliyun_client.py` 新增 `delete_file_by_name()` 方法

### v1.4.3 (2026-05-29)
- 🎨 统一群组通知格式：与频道通知风格对齐，包含资源名称、夸克链接、更新仓库、查看详情链接、资料总站、资料频道
- 🔗 群组通知新增夸克转存链接行（🔗 夸克链接：xxx）
- 📦 频道通知（notify.yml）新增资料频道链接，10个仓库统一更新

### v1.4.1 (2026-03-14)
- 修复：推广文件复制判断逻辑（空文件夹也被正确识别为文件夹）
- 修复：`list_folder_files` 返回 `tuple(is_folder, items)`

### v1.4.0 (2026-03-14)
- 修复：发布后自动触发网站更新（调用 `trigger_site_rebuild.sh`）
- 新增：本地配置文件支持（`config/secrets.env`），Token 不再硬编码
- 优化：完整的 9 步工作流自动化

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
