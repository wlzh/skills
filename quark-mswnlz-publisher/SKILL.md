---
name: quark-mswnlz-publisher
description: "Automate the full QuarkPanTool → mswnlz GitHub content publishing pipeline. Use when the user provides Quark share URLs and wants: (1) create a batch folder in Quark Drive, (2) save/copy resources into that folder, (3) copy promotional files INTO each shared resource folder, (4) generate permanent encrypted share links with random passcodes, (5) auto-classify items into mswnlz repos (book/movies/etc.) by repo descriptions, (6) append/update the target repo's YYYYMM.md and README month index, (7) git commit+push, (8) send unified Telegram notifications, and (9) force-trigger mswnlz.github.io site rebuild and return the final site URLs."
---

# quark-mswnlz-publisher

**版本**: v2.1.0

夸克网盘 + 百度网盘 → mswnlz GitHub 资源仓库 → 站点自动更新，一条龙发布。

## 更新日志

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

### v1.9.0 (2026-07-11)
- 🆕 **新增 @tgmkno 群组**：配置文件 quark-publisher.env 新增 `TG_GROUP_3_ID=@tgmkno`，通知同步推送到 tgmkno 群组
- 🔧 默认支持 4 个 TG 群组推送（v1.8.0），完全通过环境变量控制

### v1.8.0 (2026-07-04)
- 🆕 **第4个 TG 群组推送**：`mswnlz_publish.py` 新增 `TG_GROUP_4_ID` / `TG_GROUP_4_THREAD` 环境变量支持
- 🔧 默认支持 4 个群组推送，完全通过环境变量控制，无需改代码

### v1.7.0 (2026-07-03)
- 🆕 **quark_batch_run.py v2.0.0**: Save-Share 锁步模式，不再依赖目录列表顺序
  - 每个 item 保存后立即生成分享链接，捕获 title→URL 的显式映射
  - **规则**: 有 title+url → 用提供的 title；只有 url → 从 Quark 实际文件夹名取名字
  - 一个 title 下有多个 url 时，所有分享链接自动归到同一 title 下
- 🔧 **pipeline_orchestrator.py**: `_load_urls` 适配新版 title 字段，不再按 index 对位
- 🔧 **内容校验**: 名称与 URL 一一对应，防止跨资源串位
- 🧹 清理了过时的中间文件

### v1.6.0 (2026-07-03)
- 🆕 **阿里云盘完整支持**：新增 `aliyun_client.py` / `aliyun_batch_run.py`，基于 aligo SDK 实现阿里云盘转存+加密永久分享+推广文件复制
- 🆕 **三链发布**：`pipeline_orchestrator.py` 支持夸克+百度+阿里云盘三网盘混合分流、合并、统一发布
- 🆕 **三链 TG 通知**：群组通知和频道通知同时显示三个网盘的链接
- 🔀 **url_router.py** 新增 aliyundrive.com 识别路由
- 🆕 **自动上传推广文件**：阿里云盘首次自动扫码登录后，自动上传本地推广文件到网盘
- 🧩 **依赖**：项目 .venv 需安装 `aligo>=6.2.8`（pip install aligo）

### v1.5.0 (2026-07-01)
- 🆕 **百度网盘完整支持**：新增 `baidu_client.py` / `baidu_batch_run.py`，支持百度网盘转存+加密永久分享+推广文件复制
- 🆕 **统一编排器** `pipeline_orchestrator.py`：自动识别 Quark / Baidu 链接，分流处理、按名称合并结果后统一发布
- 🆕 **多链接支持**：items.json 支持 `urls` 数组，一个资源名可以同时有夸克和百度链接
- 🔗 **双链接发布**：TG 通知和群组消息同时显示夸克+百度两个链接
- 🛡️ **容错设计**：一个网盘异常不影响另一个，至少有一个链接成功即可发布
- 🔀 **统一路由** `url_router.py`：自动检测链接来源（quark.cn / pan.baidu.com）
- ♻️ 百度A段已支持文件重复时自动分享已有文件夹
- 🧪 **dry-run 模式**：编排器和发布脚本均支持 `--dry-run`，测试时可跳过 TG 通知、GitHub 推送和站点重建
- 📝 **原始标题辅助判断**：同时检查用户输入的原始标题（如"北宋帝陵 (2023) 4K 全7集"），弥补 Quark 文件夹名简写问题
- 🔧 **修复"合集"误归**：取消"合集"自动归 book 规则，防止影视合集错归书籍仓库
- ➕ 新增第三个群组到通知列表，非论坛群无 topic
- 🐛 修复：thread_id 为 None 时不传 message_thread_id 参数，避免非论坛群发送报错
- 🐛 修复：thread_id 为 None 时不传 message_thread_id 参数，避免非论坛群发送报错
- 📄 **readme 文档更新**: 分类策略新增三层文档

### v1.4.3 (2026-05-29)
- 🎨 统一群组通知格式：与频道通知风格对齐，包含资源名称、夸克链接、更新仓库、查看详情链接、资料总站、资料频道
- 🔗 群组通知新增夸克转存链接行（🔗 夸克链接：xxx）
- 📦 频道通知（notify.yml）新增资料频道链接，10个仓库统一更新

### v1.4.2 (2026-03-15)
- 🐛 修复：脚本启动时自动加载 `secrets.env` 环境变量，无需手动 export
- 📝 影响脚本：`quark_batch_run.py`、`mswnlz_publish.py`

### v1.4.1
- 初始稳定版本

## 📺 视频教程

[【资源运营神器Skills】完全开源，夸克网盘+GitHub一条龙全自动发布工具！转存、归类、TG通知、站点更新一键搞定！](https://youtu.be/s1RhLDOGOfQ)

## 📝 文字教程

[Twitter/X 教程帖子](https://x.com/gxjdian/status/2032766709711712491)

## 触发条件

当用户提供夸克分享链接并需要执行以下任一操作时：
- 批量转存夸克资源
- 生成永久加密分享链接
- 发布到 mswnlz GitHub 仓库
- 更新站点内容

## 工作区约定

| 路径 | 用途 |
|------|------|
| `/Users/m./Documents/QNSZ/project` | 项目根目录 |
| `/Users/m./Documents/QNSZ/project/QuarkPanTool` | 夸克自动化工具 |
| `/Users/m./Documents/QNSZ/project/mswnlz` | mswnlz 组织仓库 |
| `/Users/m./Documents/QNSZ/project/skills` | Skills 仓库 (wlzh/skills) |

## 安全要求

- **不要**在聊天中粘贴或回显 Token
- **优先**使用 GitHub SSH 方式（`git@github.com:...`）
- 如需 GitHub API，通过环境变量 `GITHUB_TOKEN` 传入，**不要写入文件**
- **Telegram Token 必须通过环境变量配置**（见下方）

## 环境变量配置

在运行脚本前，需要设置以下环境变量：

```bash
# Telegram Bot Token（必须）
export TELEGRAM_BOT_TOKEN="你的Bot Token"

# Telegram 群组配置（可选，用于发送通知）
export TG_GROUP_1_ID="-100XXXXXXXXXX"      # 群组 1 ID
export TG_GROUP_1_THREAD="5"               # 群组 1 话题 ID
export TG_GROUP_2_ID="-100YYYYYYYYYY"      # 群组 2 ID
export TG_GROUP_2_THREAD="2"               # 群组 2 话题 ID
export TG_GROUP_4_ID=""                     # 群组 4 ID
export TG_GROUP_4_THREAD=""                # 群组 4 话题 ID

# Telegram 频道 ID（可选）
export TELEGRAM_CHANNEL_ID="@your_channel"

# GitHub Token（可选，用于 API 调用）
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

⚠️ **安全提示**：
- 永远不要将 Token 硬编码在脚本中
- 永远不要将 Token 提交到 Git 仓库

## 完整工作流

### 0) 输入收集

需要用户提供：
- 夸克分享 URL 列表（每条可包含标题）
- 目标月份 `YYYYMM`（默认：当前月份）
- 批次标签（默认：`短裤哥批次`）

### 1) 确保各网盘登录状态

**夸克网盘**：
- 检查 `QuarkPanTool/config/cookies.txt`
- 如果不存在或为空：运行 `python quark_login.py`
- 登录流程：自动打开 Chrome → 用户扫码 → Cookie 自动保存

**阿里云盘**（首次使用需扫码）：
- 首次运行 `aliyun_batch_run.py` 时，终端会打印二维码图片链接
- 用阿里云盘 App 扫码登录后，refresh_token 自动保存到 `~/.aligo/quark-mswnlz.json`
- 后续运行自动复用 token，无需再扫码
- 首次运行还会自动上传本地推广文件到阿里云盘的 `/推广文件` 目录

### 2) 批量转存 + 生成分享链接（支持夸克/百度/阿里云盘）

```
          ┌─ 夸克 ─→ quark_batch_run.py
items.json ── 百度 ─→ baidu_batch_run.py  ──→ batch_share_results.json ──→ 合并 ──→ B段
          └─ 阿里云盘 → aliyun_batch_run.py
```

使用 `scripts/quark_batch_run.py`：
1. 在夸克根目录创建批次文件夹（格式：`YYYY-MM-DD_HHMM_<label>`）
2. 批量转存所有分享 URL 到该文件夹
3. 列出文件夹内所有项目
4. 为每个顶层项目生成分享链接：
   - `url_type=2`（加密）
   - `expired_type=1`（永久）
   - 随机提取码
5. 输出 JSON：`batch_share_results.json`

### 3) 复制推广文件到每个资源文件夹内部 🆕

使用 `scripts/copy_promo_to_folders.py`：
- 从夸克网盘的 `temp/要共享的文件` 文件夹读取推广文件
- **复制到每个转存的资源文件夹内部**（不是批次文件夹）

**重要**：推广文件会被复制到每个资源文件夹里面，这样分享出去的每个文件夹都包含推广文件。

**前提条件**：
- 需要提前在夸克网盘创建 `temp/要共享的文件` 文件夹
- 上传推广文件到该文件夹

**推广文件清单**：
- `必看免责声明_及加入资源分享群_及_副业_0_成本赚钱教程_资源网站doc_869hr_uk.txt`
- `1_解压密码869hr_uk_移动端双击这里.html`
- `0_双击获取解压密码_Mac系统双击这里.webloc`
- `0_双击获取解压密码_windows系统双击这里.url`

### 4) 自动归类到 mswnlz 仓库

使用 `scripts/mswnlz_publish.py`：
1. 调用 GitHub API 获取 mswnlz 组织仓库列表
2. 根据标题关键词分层归类（v1.4.4）：
   - **第一关 视频/影视类**：命中分辨率（4K/超清/蓝光/1080P）、影视短语（电影/纪录片/电视剧）、集数标识（全X集/第X集）、视频后缀 → `movies`
   - **第二关 书籍类**：书/书单/新书/电子书/杂志、X册/X本 → `book`（不再用"合集"归书）
   - **第三关 回退匹配**：前两关未命中时，根据仓库 description 关键词模糊评分
3. 克隆/更新本地仓库（SSH 方式）
4. 追加到 `<YYYYMM>.md`：
   ```
   - {标题}-超过100T资料总站网站-doc.869hr.uk | {分享链接}
   ```
5. 更新 `README.md` 月份索引（保持倒序）
6. Git commit + push
7. **发送统一的 Telegram 群组通知**（多仓库更新只发一条汇总消息）

### 5) 触发站点重建

使用 `scripts/trigger_site_rebuild.sh`：
1. 在 `mswnlz.github.io` 仓库创建空提交
2. Push 到 main 分支
3. 触发 GitHub Actions 构建

### 6) 返回结果

返回给用户：
- 批次文件夹名称
- 所有分享链接（含提取码）
- 每个项目的目标仓库 + 文件路径
- Actions 运行 URL
- 站点 URL（https://doc.869hr.uk）

### 7) 生成夸克群组消息 🆕

在 `mswnlz_publish.py` 执行后：
1. 自动生成格式化的消息
2. 保存到 `quark_group_message.txt`
3. 控制台输出，方便复制

**消息格式**：
```
📦 资源更新通知

📚 书籍资料
------------------------------
• 2026.3.3小说合集推荐
  🔗 https://pan.quark.cn/s/xxx?pwd=xxx

========================================
🌐 资料总站：https://doc.869hr.uk
📂 批次文件夹：2026-03-14_1700_短裤哥批次
📊 共 1 项资源
```

**使用方式**：
1. 脚本运行完成后，复制消息内容
2. 打开夸克 APP → 群组（2122364648、2026346189）
3. 粘贴发送

## Telegram 通知机制

### 频道通知（@dabaziyuan）
- **每条资源单独发送**
- 包含：资源名称 + GitHub 链接
- 由 GitHub Workflow 自动触发

### 群组通知（tgmShare 话题5、tgmShareAI 话题2、群组4）
- **批量更新只发一条汇总消息**
- 格式与频道风格对齐：📦 新增资源推送 + 资源名称 + 夸克链接 + 更新仓库 + 查看详情 + 资料总站 + 资料频道
- 由 Skills 脚本统一发送，避免刷屏

### 夸克群组消息 🆕
- **手动复制发送**（夸克无公开 API）
- 群号：2122364648、2026346189
- 格式：资源名称 + 链接 + 资料总站
- 自动生成并保存到 `quark_group_message.txt`

## 脚本说明

### scripts/quark_batch_run.py

夸克批量转存 + 生成分享链接。

```bash
python scripts/quark_batch_run.py \
  --label "短裤哥批次" \
  --month 202603 \
  --items-json items.json \
  --out-json batch_share_results.json
```

**依赖**：
- QuarkPanTool 环境（`.venv`）
- 夸克 Cookie（`config/cookies.txt`）

### scripts/copy_promo_to_folders.py 🆕

复制推广文件到每个资源文件夹内部。

```bash
python scripts/copy_promo_to_folders.py \
  --batch-json batch_share_results.json
```

**工作原理**：
1. 读取 `batch_share_results.json` 中的 `share_results`
2. 对于每个分享结果，检查其 `fid` 是否是文件夹
3. 如果是文件夹，复制推广文件**到文件夹内部**

**注意**：推广文件会被复制到每个资源文件夹里面，这样每个分享的文件夹都包含推广文件。

### scripts/quark_copy.py (已废弃)

此脚本已被 `copy_promo_to_folders.py` 替代。

### scripts/cleanup_junk_files.py 🆕 v2.0.0

垃圾文件清理脚本：扫描批次文件夹下所有子文件夹，删除原分享者植入的推广/广告文件。

```bash
python scripts/cleanup_junk_files.py \
  --batch-json batch_share_results.json \
  --junk-config config/junk_files.json \
  --baidu-batch-path /短裤哥批次/2026-07-15_0816_短裤哥批次
```

**参数**：
- `--batch-json`: batch_share_results.json 路径
- `--junk-config`: junk_files.json 配置路径
- `--quark-parent-fid`: 夸克批次文件夹的父目录 FID（默认 0=根目录）
- `--baidu-batch-path`: 百度批次文件夹路径

**工作原理**：
1. 加载垃圾文件名列表（支持子串匹配）
2. 连接夸克/百度/阿里云客户端
3. 遍历批次文件夹下所有子文件夹
4. 删除匹配名单的垃圾文件
5. **不重新生成分享链接**（夸克分享链接动态反映文件夹内容）

**配置文件 `config/junk_files.json`**：
```json
{
  "files": [
    "🌹更多资源共享群🌹.jpg",
    "影视ju风小程序剪辑课截图.jpg",
    ...
  ]
}
```

随时可追加新的垃圾文件名，pipeline 运行时自动读取最新配置。

### scripts/mswnlz_publish.py

发布到 GitHub 仓库 + 发送 Telegram 群组通知。

```bash
python scripts/mswnlz_publish.py \
  --month 202603 \
  --batch-json batch_share_results.json
```

支持 `--dry-run` 参数（测试时跳过推送）：

```bash
python scripts/mswnlz_publish.py \
  --month 202603 \
  --batch-json batch_share_results.json \
  --dry-run
```

**依赖**：
- Git SSH 配置
- 可选：`GITHUB_TOKEN` 环境变量

### scripts/pipeline_orchestrator.py 🆕

统一编排器：自动识别 Quark/Baidu 链接，分流处理、合并结果后统一发布。

```bash
# 完整发布
python scripts/pipeline_orchestrator.py \
  --items-json items.json \
  --label "短裤哥批次"

# 测试（只跑转存+分享+合并，不发布）
python scripts/pipeline_orchestrator.py \
  --items-json items.json \
  --label "短裤哥批次" \
  --dry-run
```

**items.json 新增格式**（支持多链接）：

```json
{
  "title": "樊登讲书2026年合集【全网最新】",
  "urls": [
    "https://pan.quark.cn/s/7f6be305d850",
    "https://pan.baidu.com/s/1YHBDynfOKAkxpEjQzDq0Gg?pwd=L6kA"
  ]
}
```

旧格式 `url` 仍兼容：

```json
{
  "title": "泰坦尼克号",
  "url": "https://pan.quark.cn/s/c2bf2c29b114"
}
```

**依赖**：
- 所有 Quark A段 依赖
- 所有 Baidu A段 依赖
- `url_router.py`（本仓库）
- QuarkPanTool 需放在与 `skills/` 同级的目录下

### scripts/url_router.py 🆕

自动检测链接来源（quark.cn / pan.baidu.com）。

### scripts/baidu_batch_run.py 🆕（位于 QuarkPanTool 仓库）

百度网盘 A段：批量转存 + 加密永久分享 + 推广文件复制。详见 [QuarkPanTool 下的 Baidu 模块](#quarkpantool-百度模块)。

## 新机器安装指南

### 1. 克隆仓库

```bash
# skills 仓库（发布脚本）
git clone git@github.com:wlzh/skills.git

# QuarkPanTool（转存脚本，用 gxjda 的 fork，含百度支持）
git clone git@github.com:gxjda/QuarkPanTool.git
cd QuarkPanTool
git checkout feat/baidu-support
```

两个仓库需放在同一父目录下：

```
/你的工作目录/
├── QuarkPanTool/         # 转存脚本（含百度支持）
└── skills/               # 发布脚本
    └── quark-mswnlz-publisher/
        └── scripts/
```

### 2. 安装依赖

**百度网盘**（BaiduPCS-Go）：
```bash
# 下载 BaiduPCS-Go v4.0.1+
# https://github.com/qjfoidnh/BaiduPCS-Go/releases
# macOS ARM64 版本：
wget https://github.com/qjfoidnh/BaiduPCS-Go/releases/download/v4.0.1/BaiduPCS-Go-v4.0.1-darwin-arm64.zip
unzip BaiduPCS-Go-v4.0.1-darwin-arm64.zip
# 放到 PATH 下
chmod +x /path/to/BaiduPCS-Go
# 登录
BaiduPCS-Go login -bduss=你的BDUSS -stoken=你的STOKEN
```

**夸克网盘**（QuarkPanTool 虚拟环境）：
```bash
cd QuarkPanTool
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置凭证

| 文件 | 用途 | 位置 |
|------|------|------|
| `config/baidu_auth.json` | BDUSS/STOKEN（百度盘） | `QuarkPanTool/config/` |
| `config/cookies.txt` | Quark Cookie（夸克盘） | `QuarkPanTool/config/` |
| `~/.mp-publisher/config.json` | TG Bot Token / 群组配置 | （来自 mp-article-publisher） |

### 4. 上传推广文件

**夸克盘**：上传到 `temp/要共享的文件` 目录（QuarkPanTool 默认创建）。
**百度盘**：上传到 `/推广文件/` 目录，文件清单同夸克。

## 脚本说明
