# quark-mswnlz-publisher

**版本**: v2.2.0

夸克网盘 / 百度网盘 / 阿里云盘 → mswnlz GitHub 资源仓库 → 站点自动更新，一条龙发布。

支持三网盘混合输入、多账号轮换、多群组通知。

---

## 📺 视频教程

**【资源运营神器 Skills】完全开源，夸克网盘 + GitHub 一条龙全自动发布工具 (v1.2.0)！**

👉 [YouTube 视频教程](https://youtu.be/s1RhLDOGOfQ)

## 📝 文字教程

👉 [Twitter/X 文字教程](https://x.com/gxjdian/status/2032766709711712491)

---

## 🎯 功能概述

| 功能 | 说明 |
|------|------|
| 三网盘转存 | 夸克 / 百度 / 阿里云盘混合输入，自动识别 URL 分流 |
| 多账号轮换 🆕 | 夸克多账号按批次自动轮换，分摊转存压力 |
| 推广文件复制 | 从模板文件夹复制推广文件到**每个资源文件夹内部** |
| 垃圾文件清理 🆕 | 自动删除资源文件夹内的广告图、引导图等垃圾文件 |
| 自动生成分享链接 | 永久有效期 + 加密链接 + 随机提取码 |
| 智能分类 | 三层关键词策略，自动归类到 book/movies/AIknowledge 等仓库 |
| 自动落盘 | 追加/新建 `YYYYMM.md` + 更新 README 月份索引 |
| 自动提交 | commit + push 到 GitHub mswnlz 仓库 |
| Telegram 通知 | 频道单条 + 多群组汇总通知 |
| 站点重建 | 构建校验通过后触发 `mswnlz.github.io` Pages 重建 |
| SEO 兼容 | 只写资源源文件，站点通过构建期 catalog 生成检索目录 |

---

## 📐 架构总览

```
用户输入 items.json
        │
        ▼
┌───────────────────────┐
│ pipeline_orchestrator  │   ← 统一编排器（主入口）
└───────┬───────────────┘
        │ url_router.py 按 URL 自动分流
        ├────────────────┬─────────────────┐
        ▼                ▼                 ▼
   ┌─────────┐     ┌─────────┐      ┌───────────┐
   │ 夸克 A段 │     │ 百度 A段 │      │ 阿里云 A段 │
   │ (转存+   │     │ (转存+   │      │ (转存+    │
   │  分享+   │     │  分享+   │      │  分享+    │
   │ 账号轮换) │     │  推广)   │      │  推广)    │
   └────┬────┘     └────┬────┘      └─────┬─────┘
        │                │                 │
        ▼                ▼                 ▼
┌─────────────────────────────────────────────┐
│        合并结果（按资源名匹配多网盘链接）        │
└─────────────────────┬───────────────────────┘
                      │
        ▼             ▼             ▼
  ┌──────────┐ ┌──────────┐ ┌────────────┐
  │ 清理垃圾  │ │ 推广文件  │ │  分类发布   │
  │ 文件     │ │  复制    │ │ (GitHub +  │
  │          │ │          │ │  TG通知 +  │
  └──────────┘ └──────────┘ │  站点重建)  │
                            └────────────┘
```

---

## 📦 环境要求

### 系统要求
- macOS / Linux
- Python 3.10+
- Git（配置 SSH 访问 GitHub mswnlz 组织仓库）
- Chrome/Chromium 浏览器（夸克登录用 Playwright）

### 外部依赖

#### 1. QuarkPanTool（夸克网盘自动化工具）

基于 [ihmily/QuarkPanTool](https://github.com/ihmily/QuarkPanTool)，本项目对其进行了扩展。

```bash
cd /path/to/project
git clone https://github.com/ihmily/QuarkPanTool.git
cd QuarkPanTool

python3 -m venv .venv
. .venv/bin/activate

pip install -r requirements.txt
# requirements.txt:
#   httpx
#   retrying==1.3.4
#   prettytable==3.10.0
#   playwright==1.43.0
#   tqdm>=4.66.3
#   colorama

playwright install chromium
```

**核心文件**：
- `quark.py` — 夸克网盘核心操作（转存、分享、删除、复制、列目录）
- `quark_login.py` — Playwright 扫码登录，获取 Cookie

#### 2. BaiduPCS-Go（百度网盘 CLI）

百度网盘转存依赖 [BaiduPCS-Go](https://github.com/qjfoidnh/BaiduPCS-Go)。

```bash
# macOS
brew install baidupcs-go
# 或从 Release 下载二进制放到 /usr/local/bin/
```

验证：`BaiduPCS-Go --version`

**核心文件**（在 QuarkPanTool/ 下）：
- `baidu_client.py` — BaiduPCS-Go CLI 封装（转存、分享、复制、删除）
- `baidu_batch_run.py` — 百度 A段批处理

⚠️ 已知问题：百度转存的文件名可能出现乱码，但分享链接正常。

#### 3. aligo（阿里云盘 SDK）

阿里云盘转存依赖 [aligo](https://github.com/foyoux/aligo)。

```bash
cd QuarkPanTool && . .venv/bin/activate
pip install aligo   # 已在 .venv 中
```

**核心文件**（在 QuarkPanTool/ 下）：
- `aliyun_client.py` — aligo SDK 封装（登录、转存、分享、复制、删除）
- `aliyun_batch_run.py` — 阿里云 A段批处理

#### 4. GitHub SSH 配置

```bash
ssh -T git@github.com
# Hi username! You've successfully authenticated...
```

需可访问 mswnlz 组织仓库（read/write）。

### 目录结构（默认路径）

```
/path/to/project/
├── QuarkPanTool/                      # 网盘自动化工具（夸克+百度+阿里云）
│   ├── .venv/                         # Python 虚拟环境
│   ├── quark.py                       # 夸克核心库
│   ├── quark_login.py                 # 夸克登录脚本
│   ├── baidu_client.py                # 百度网盘 CLI 封装
│   ├── baidu_batch_run.py             # 百度 A段批处理
│   ├── aliyun_client.py               # 阿里云盘 SDK 封装
│   ├── aliyun_batch_run.py            # 阿里云 A段批处理
│   ├── batch_runner.py                # 通用批处理工具
│   ├── config/
│   │   ├── cookies.txt                # 当前激活的夸克 Cookie（轮换器维护）
│   │   ├── cookies_1.txt              # 账号1 Cookie
│   │   ├── cookies_2.txt              # 账号2 Cookie
│   │   ├── cookies.txt.bak            # 切换前备份
│   │   ├── account_state.json         # 多账号轮换状态
│   │   ├── config.json                # 保存目录配置
│   │   └── secrets.env                # 敏感信息（TG Token、GH Token、群组ID）
│   └── ...
├── mswnlz-github/                     # mswnlz GitHub 组织仓库（本地 clone）
│   ├── book/                          # 书籍资源
│   ├── movies/                        # 影视资源
│   ├── AIknowledge/                   # AI 知识资源
│   ├── curriculum/                    # 课程资源
│   ├── tools/                         # 工具资源
│   ├── edu-knowlege/                  # 教育资源
│   ├── healthy/                       # 健康资源
│   ├── self-media/                    # 自媒体资源
│   ├── cross-border/                  # 跨境资源
│   ├── chinese-traditional/           # 国学资源
│   ├── auto/                          # 汽车资源
│   └── mswnlz.github.io/              # 站点仓库（GitHub Pages）
└── skills/
    └── quark-mswnlz-publisher/        # 本 Skill
        ├── SKILL.md
        ├── README.md
        ├── promo_files/               # 推广文件本地备份
        ├── references/
        │   └── mswnlz-repos-cache.json
        └── scripts/
            ├── pipeline_orchestrator.py   # ⭐ 统一编排器
            ├── quark_batch_run.py          # 夸克 A段
            ├── quark_account_rotator.py    # 多账号轮换器
            ├── copy_promo_to_folders.py    # 推广文件复制
            ├── cleanup_junk_files.py       # 垃圾文件清理
            ├── mswnlz_publish.py           # GitHub 发布 + TG 通知
            ├── url_router.py               # 网盘链接路由
            ├── trigger_site_rebuild.sh     # 站点重建
            ├── quark_copy.py               # 旧版夸克复制（已由 copy_promo 替代）
            └── config/
                └── junk_files.json         # 垃圾文件名单
```

---

## 🔧 配置

### secrets.env

路径：`QuarkPanTool/config/secrets.env`

```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...       # TG Bot Token
TELEGRAM_CHANNEL_ID=@dabaziyuan            # TG 频道

# 群组通知（最多4组）
TG_GROUP_1_ID=-100xxxxxxxxxx               # 群组1 ID
TG_GROUP_1_THREAD=5                        # 群组1 话题 ID
TG_GROUP_2_ID=-100yyyyyyyyyy               # 群组2 ID
TG_GROUP_2_THREAD=2                        # 群组2 话题 ID
TG_GROUP_3_ID=@tgmkno                      # 群组3（频道格式，无 topic）
TG_GROUP_3_THREAD=
TG_GROUP_4_ID=-100zzzzzzzzzz               # 群组4 ID
TG_GROUP_4_THREAD=235                      # 群组4 话题 ID

# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxx              # mswnlz 账户的 GitHub Token
```

### items.json

路径：`scripts/items.json`（每次执行前更新）

```json
[
  {"title": "300集口语动画", "url": "https://pan.quark.cn/s/xxx"},
  {"title": "泰坦尼克号 4K", "url": "https://pan.quark.cn/s/yyy"},
  {"title": "mixed resource",
   "urls": [
     "https://pan.quark.cn/s/quark_link",
     "https://pan.baidu.com/s/baidu_link?pwd=xxxx"
   ]
  }
]
```

> `url`（单个）和 `urls`（数组）两种格式都支持，可混用。

### junk_files.json

路径：`scripts/config/junk_files.json`

```json
{
  "files": [
    "🌹更多资源共享群🌹.jpg",
    "免费分享群.jpg",
    "更多精彩资源点这里.txt"
  ]
}
```

匹配方式：**子串匹配**（名单中的任意字符串出现在文件名中即删除）。

---

## 🚀 使用方式

### 一键执行（推荐）

```bash
cd /path/to/QuarkPanTool
. .venv/bin/activate

python /path/to/pipeline_orchestrator.py \
  --items-json /path/to/items.json \
  --label "短裤哥批次"
```

编排器自动完成：
1. 读取 items.json，按 URL 分流到夸克/百度/阿里云
2. 每个网盘独立执行转存+分享（夸克自动轮换账号）
3. 按资源名合并多网盘结果
4. 清理垃圾文件
5. 复制推广文件
6. 分类推送到 GitHub mswnlz 仓库
7. 发送 TG 群组通知
8. 触发站点重建

### 模拟运行

```bash
python pipeline_orchestrator.py --items-json items.json --label "测试" --dry-run
```

### 分步执行

**夸克转存+分享**：
```bash
python quark_batch_run.py \
  --items-json items.json \
  --label "短裤哥批次" \
  --month 202607 \
  --out-json quark_result.json
```

**百度转存+分享**：
```bash
python baidu_batch_run.py \
  --items-json items.json \
  --label "短裤哥批次" \
  --month 202607 \
  --out-json baidu_result.json
```

**阿里云转存+分享**：
```bash
python aliyun_batch_run.py \
  --items-json items.json \
  --label "短裤哥批次" \
  --month 202607 \
  --out-json aliyun_result.json
```

**推广文件复制**：
```bash
python copy_promo_to_folders.py --batch-json quark_result.json
```

**发布到 GitHub + TG 通知**：
```bash
python mswnlz_publish.py \
  --month 202607 \
  --batch-json batch_share_results.json
```

---

## 👥 多账号轮换 🆕 v2.1.0

支持多个夸克账号**按批次自动轮换**，分摊转存压力，避免单账号被限速。

### 工作原理

- **方案B（按批次轮换）**：每次执行自动切到下一个账号
- **做法甲（cookie 文件复制）**：将 `cookies_N.txt` 复制为 `cookies.txt`，`quark.py` 零改动

### 配置

1. 登录每个账号获取 Cookie：
```bash
cd QuarkPanTool && . .venv/bin/activate
python quark_login.py   # 登录账号1
cp config/cookies.txt config/cookies_1.txt

python quark_login.py   # 登录账号2
cp config/cookies.txt config/cookies_2.txt
```

2. 每个账号网盘里需要有 `temp/要共享的文件/` 推广文件模板

3. 无需其他配置，执行时自动轮换

### 使用

```bash
# 正常（自动轮换）
python quark_batch_run.py --items-json items.json ...

# 强制指定账号
python quark_batch_run.py --force-account 1 ...

# 跳过轮换
python quark_batch_run.py --no-rotate ...
```

### 管理命令

```bash
cd QuarkPanTool && . .venv/bin/activate

python scripts/quark_account_rotator.py --config-dir ./config status   # 状态
python scripts/quark_account_rotator.py --config-dir ./config next     # 手动轮换
python scripts/quark_account_rotator.py --config-dir ./config list     # 列出账号
python scripts/quark_account_rotator.py --config-dir ./config force 2  # 强制切换
```

---

## 🧹 垃圾文件清理

`cleanup_junk_files.py` 在转存后、分享前自动清理广告/引导文件，支持夸克/百度/阿里云三端。

配置见 `scripts/config/junk_files.json`（子串匹配）。

---

## 📎 推广文件机制

### 工作原理

1. 每个账号网盘中创建 `temp/要共享的文件/` 文件夹，上传推广文件
2. 脚本从模板文件夹复制推广文件到每个资源文件夹内部
3. 夸克：`file/copy` API 同账号内复制
4. 百度：BaiduPCS-Go `cp` 命令
5. 阿里云：aligo SDK

### 推广文件模板

| 文件名 | 用途 |
|--------|------|
| `必看免责声明-及加入资源分享群 及 副业 0 成本赚钱教程-资源网站doc.869hr.uk.txt` | 免责声明 + 联系方式 |
| `1.【解压密码869hr.uk】-移动端双击这里-资源网站doc.869hr.uk.html` | 移动端解压密码 |
| `0.【双击获取解压密码】-Mac系统双击这里-资源网站doc.869hr.uk.webloc` | Mac 快捷方式 |
| `0.【双击获取解压密码】-windows系统双击这里-资源网站doc.869hr.uk.url` | Windows 快捷方式 |
| `【！！！注意】一定要保存到自己的盘，防止失效！！！-资源网站doc.869hr.uk` | 保存提醒 |

夸克推广文件夹 fid 从 v2.1.1 起改为**动态发现**（先试硬编码 → 失败则在 `temp/` 下按名称查找），自动适配多账号。

本地备份：`promo_files/` 目录。

---

## 📢 发布 + 通知 + 站点重建

### GitHub 发布
- 自动分类到 mswnlz 仓库（12 个仓库）
- 追加到 `YYYYMM.md`，更新 `README.md` 月份索引
- commit + push（SSH 认证）

### 分类规则（v1.4.4 三层策略）

**第一关：视频/影视类 → movies**
- 分辨率：4K / 超清 / 蓝光 / 高清 / 1080P / 2160P / 720P
- 影视：电影 / 纪录片 / 演唱會 / 电视剧 / 剧集 / 连续剧
- 集数：全X集 / 第X集 / X集全 / X集完结
- 后缀：.mp4 / .mkv / .avi / .rmvb / .mov

**第二关：书籍类 → book**
- 书 / 书单 / 新书 / 电子书 / 杂志 / X册 / X本

**第三关：回退评分**
- 按仓库 description 关键词打分（curriculum / tools / healthy / AIknowledge 等）

### Telegram 通知

**频道（@dabaziyuan）**：
- 每条资源单独发送
- 由 GitHub Workflow 自动触发

**群组（最多4组，可配 topic）**：
- 批量更新只发一条汇总消息
- 包含：资源名称 + 夸克链接 + 更新仓库 + 查看详情 + 资料总站 + 资料频道

### 站点 SEO 与设计合同

资源站点已重构为检索优先的 VitePress 目录页，设计依据 `taste-skill:design-taste-frontend`：
- 分类首页不再按月份 Tab 切换，而是由构建期 catalog 生成可搜索、可筛选目录
- 月份页继续保留为 `/category/YYYYMM` 归档 URL
- 发布脚本只追加内容仓库的 `YYYYMM.md`，不生成分类首页、不写 `ResourceTabs :months`、不写广告容器
- 新资源行使用 Markdown 链接格式：`[标题](分享链接)`
- `docs/public/{category}/*.md` 是旧重复页面来源，发布链路不得重新生成

### 站点重建
- 触发脚本会先定位 `mswnlz.github.io` 仓库，可用 `MSWNLZ_SITE_REPO` 覆盖
- 执行 `npm run build` 和 `npm run validate`
- 校验通过后创建空 commit + push，GitHub Pages 自动重建
- 本地 `dist` 和 catalog 构建噪音不会被提交

---

## 📊 全流程数据流

```
items.json
    │
    ├──→ quark_batch_run.py ──→ quark_result.json ──┐
    ├──→ baidu_batch_run.py ──→ baidu_result.json ──┤
    └──→ aliyun_batch_run.py ──→ aliyun_result.json ┤
                                                     │
              pipeline_orchestrator.py               │
              (merge_results 按资源名合并)  ←──────────┘
                        │
                        ▼
              batch_share_results.json
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
   cleanup_junk   copy_promo    mswnlz_publish
                                    │
                          ┌─────────┼─────────┐
                          ▼         ▼         ▼
                      GitHub    Telegram   站点重建
                      仓库推送   群组通知    (Pages)
```

---

## 📝 脚本版本一览

| 脚本 | 版本 | 说明 |
|------|------|------|
| pipeline_orchestrator.py | 1.2.0 | 统一编排器 |
| quark_batch_run.py | 2.1.0 | 夸克转存+分享+多账号轮换 |
| quark_account_rotator.py | 1.0.0 | 多账号轮换器 |
| baidu_client.py | 1.1.0 | 百度网盘 CLI 封装 |
| baidu_batch_run.py | 1.1.0 | 百度转存+分享 |
| aliyun_client.py | 1.0.0 | 阿里云盘 SDK 封装 |
| aliyun_batch_run.py | 1.0.0 | 阿里云转存+分享 |
| copy_promo_to_folders.py | 2.1.1 | 推广文件复制（动态 fid） |
| cleanup_junk_files.py | 1.0.0 | 垃圾文件清理 |
| mswnlz_publish.py | 1.1.0 | GitHub 发布 + TG 通知 + SEO 资源格式 |
| url_router.py | 1.1.0 | 网盘链接路由 |

---

## 📜 更新日志

### v2.2.0 (2026-07-24)
- 同步站点 SEO 重构后的发布合同：只写资源源文件，站点分类页由 catalog 生成
- `mswnlz_publish.py` 新资源写入格式改为 `[标题](URL)`，避免标题后缀污染目录页
- `trigger_site_rebuild.sh` 在触发 Pages 前执行 build + validate，并避免提交 dist/catalog 噪音
- 默认本地内容仓库路径更新为 `/Users/m/document/QNSZ/project/mswnlz-github`

### v2.1.1 (2026-07-19)
- 🔧 copy_promo 动态发现推广文件夹 fid，自动适配多账号
- 📝 README 全面重写，覆盖三网盘完整能力 + 依赖说明

### v2.1.0 (2026-07-19)
- 🆕 多账号轮换：`quark_account_rotator.py` + `quark_batch_run.py` 集成
- 支持 `--force-account` / `--no-rotate` 参数
- 输出 JSON 新增 `quark_account` 字段

### v2.0.0 (2026-07-15)
- 重构为多网盘统一编排架构
- 新增阿里云盘支持（aligo SDK）
- 新增垃圾文件清理模块
- pipeline_orchestrator 支持 dry-run

### v1.4.4
- 智能分类升级：三层关键词策略 + 原始标题辅助判断

### v1.4.3 (2026-05-29)
- 统一群组通知格式，与频道风格对齐
- 群组通知新增夸克转存链接

### v1.4.1 (2026-03-14)
- 修复推广文件复制判断逻辑

### v1.4.0 (2026-03-14)
- 新增本地配置文件支持（secrets.env）
- 完整 9 步工作流自动化

### v1.3.0 (2026-03-14)
- 推广文件复制到每个资源文件夹内部
- 新增视频教程和文字教程链接

### v1.2.0 (2026-03-14)
- 新增推广文件复制功能
- 新增 Telegram 群组汇总通知

### v1.0.0 (2026-03-14)
- 初始版本

---

## 🔗 相关链接

- **QuarkPanTool**：https://github.com/ihmily/QuarkPanTool
- **BaiduPCS-Go**：https://github.com/qjfoidnh/BaiduPCS-Go
- **aligo**：https://github.com/foyoux/aligo
- **mswnlz 组织**：https://github.com/mswnlz
- **站点地址**：https://doc.869hr.uk
- **Skills 仓库**：https://github.com/wlzh/skills
- **Telegram 频道**：https://t.me/dabaziyuan
