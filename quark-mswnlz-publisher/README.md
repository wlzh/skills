# quark-mswnlz-publisher

**版本**: v2.1.1

夸克网盘 / 百度网盘 / 阿里云盘 → mswnlz GitHub 资源仓库 → 站点自动更新，一条龙发布。

---

## 🎯 核心能力

一条命令完成从「分享链接」到「资料站上线」的全流程：

1. **转存**：自动把夸克/百度/阿里云盘的分享资源转存到自己的网盘
2. **分享**：为每个资源生成永久加密分享链接（随机提取码）
3. **清理**：自动删除资源文件夹内的垃圾文件（广告图、引导图等）
4. **推广**：把推广文件（公众号二维码等）复制进每个资源文件夹
5. **发布**：按类别推送到 mswnlz GitHub 仓库，触发站点重建
6. **通知**：向多个 Telegram 群组发送资源更新通知

支持**三个网盘**混合输入、**多账号轮换**、**多群组通知**。

---

## 📐 架构总览

```
用户输入 items.json
        │
        ▼
┌───────────────────┐
│ pipeline_orchestrator.py   │   ← 统一编排器（入口）
└───────┬───────────┘
        │ 分流：按 URL 自动识别网盘来源
        ├────────────────┬─────────────────┐
        ▼                ▼                 ▼
   ┌─────────┐     ┌─────────┐      ┌───────────┐
   │ 夸克 A段 │     │ 百度 A段 │      │ 阿里云 A段 │
   │ (转存+   │     │ (转存+   │      │ (转存+    │
   │  分享)   │     │  分享)   │      │  分享)    │
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

## 🗂️ 目录结构

```
quark-mswnlz-publisher/
├── README.md
├── SKILL.md
├── promo_files/               # 推广文件模板（备用）
├── references/                # 参考文档
└── scripts/
    ├── pipeline_orchestrator.py   # ⭐ 统一编排器（主入口）
    ├── quark_batch_run.py          # 夸克 A段：转存 + 分享
    ├── quark_account_rotator.py    # 🆕 多账号轮换器
    ├── baidu_batch_run.py          # 百度 A段（在 QuarkPanTool/ 下）
    ├── aliyun_batch_run.py         # 阿里云盘 A段（在 QuarkPanTool/ 下）
    ├── cleanup_junk_files.py       # 🧹 垃圾文件清理
    ├── copy_promo_to_folders.py    # 📎 推广文件复制（夸克/百度/阿里云）
    ├── mswnlz_publish.py           # 📢 发布到 GitHub + TG 通知 + 站点重建
    ├── trigger_site_rebuild.sh     # 🌐 触发 GitHub Pages 重建
    ├── url_router.py               # 🔗 网盘链接类型路由
    ├── quark_copy.py               # 旧版夸克文件复制（已由 copy_promo 替代）
    ├── config/
    │   └── junk_files.json         # 垃圾文件名单（子串匹配）
    ├── items.json                  # 输入文件（当前批次资源列表）
    └── batch_share_results.json    # 输出文件（转存+分享结果）
```

**外部依赖**：
```
QuarkPanTool/                     # 基于 ihmily/QuarkPanTool
├── quark.py                      # 夸克网盘核心操作
├── quark_login.py                # 夸克登录（Playwright 扫码）
├── baidu_client.py               # 百度网盘客户端
├── aliyun_client.py              # 阿里云盘客户端
├── batch_runner.py               # 通用批处理工具
├── config/
│   ├── cookies.txt               # 当前激活的夸克 cookie
│   ├── cookies_1.txt             # 账号1 cookie
│   ├── cookies_2.txt             # 账号2 cookie
│   ├── cookies.txt.bak           # 切换前备份
│   ├── account_state.json        # 多账号轮换状态
│   ├── config.json               # 保存目录配置
│   └── secrets.env               # 敏感信息（TG Token、GH Token、群组ID）
└── .venv/                        # Python 虚拟环境
```

---

## 🚀 使用方式

### 一键执行（推荐）

准备 `items.json`：
```json
[
  {
    "title": "300集口语动画",
    "urls": ["https://pan.quark.cn/s/xxx"]
  },
  {
    "title": "泰坦尼克号 4K",
    "url": "https://pan.quark.cn/s/yyy"
  },
  {
    "title": " mixed resource",
    "urls": [
      "https://pan.quark.cn/s/quark_link",
      "https://pan.baidu.com/s/baidu_link?pwd=xxxx"
    ]
  }
]
```

> `url`（单链接）和 `urls`（多链接数组）两种格式都支持，可混用。

运行：
```bash
cd /Users/m./Documents/QNSZ/project/QuarkPanTool
. .venv/bin/activate
python /path/to/pipeline_orchestrator.py \
  --items-json /path/to/items.json \
  --label "短裤哥批次"
```

编排器会自动：
1. 读取 items.json，按 URL 分流到夸克/百度/阿里云
2. 每个网盘独立执行转存+分享（夸克自动轮换账号）
3. 按资源名合并多网盘结果
4. 清理垃圾文件
5. 复制推广文件
6. 分类推送到 GitHub mswnlz 仓库
7. 发送 TG 群组通知
8. 触发站点重建

### 模拟运行（不发布）

```bash
python pipeline_orchestrator.py --items-json items.json --label "测试" --dry-run
```

### 单独执行某一步

**只跑夸克转存+分享**：
```bash
python quark_batch_run.py \
  --items-json items.json \
  --label "短裤哥批次" \
  --month 202607 \
  --out-json quark_result.json
```

**只跑发布**：
```bash
python mswnlz_publish.py \
  --month 202607 \
  --batch-json batch_share_results.json
```

**只复制推广文件**：
```bash
python copy_promo_to_folders.py \
  --batch-json quark_result.json
```

---

## 👥 多账号轮换 🆕 v2.1.0

支持多个夸克账号**按批次自动轮换**，分摊转存压力，避免单账号被限速。

### 工作原理

- **方案B（按批次轮换）**：每次执行自动切到下一个账号
- **做法甲（cookie 文件复制）**：将下一个账号的 `cookies_N.txt` 复制为 `cookies.txt`，`quark.py` 零改动

### 配置

1. 登录每个账号，获取完整 cookie：
```bash
cd QuarkPanTool && . .venv/bin/activate
python quark_login.py   # 登录账号1
cp config/cookies.txt config/cookies_1.txt

python quark_login.py   # 登录账号2
cp config/cookies.txt config/cookies_2.txt
```

2. 每个账号的网盘里需要有 `temp/要共享的文件/` 推广文件模板（copy_promo 会动态发现）

3. 无需其他配置，`quark_batch_run.py` 执行时自动轮换

### 使用

```bash
# 正常（自动轮换到下一个账号）
python quark_batch_run.py --items-json items.json ...

# 强制指定账号（某账号被限速时）
python quark_batch_run.py --force-account 1 ...

# 跳过轮换（使用当前 cookies.txt）
python quark_batch_run.py --no-rotate ...
```

### 管理命令

```bash
cd QuarkPanTool && . .venv/bin/activate

# 查看轮换状态
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
| `config/cookies_N.txt` | 更多账号（自动扫描发现） |
| `config/cookies.txt` | 当前激活的 cookie（轮换器自动维护） |
| `config/cookies.txt.bak` | 切换前的备份 |
| `config/account_state.json` | 轮换状态（当前账号、历史记录） |

---

## 🧹 垃圾文件清理

转存资源时常带有广告图、引导图等垃圾文件。`cleanup_junk_files.py` 在转存后、分享前自动清理。

**配置文件**：`scripts/config/junk_files.json`
```json
{
  "files": [
    "🌹更多资源共享群🌹.jpg",
    "免费分享群.jpg",
    "更多精彩资源点这里.txt"
  ]
}
```

匹配方式：**子串匹配**（垃圾名单中的任意字符串出现在文件名中即删除）。

支持夸克、百度、阿里云盘三个平台。

---

## 📎 推广文件复制

`copy_promo_to_folders.py` 把推广文件（公众号二维码、引导关注图等）复制进每个资源文件夹。

- **夸克**：通过 `file/copy` API 在同账号内复制
- **百度**：通过 BaiduPCS-Go `cp` 命令复制
- **阿里云盘**：通过 aliyun_client 复制

推广文件位置：`temp/要共享的文件/`（每个账号网盘里需要有一份）。

夸克推广文件夹 fid 从 v2.1.1 起改为**动态发现**（先试硬编码 → 失败则在 `temp/` 下按名称查找），自动适配多账号。

---

## 📢 发布到 GitHub + Telegram + 站点

`mswnlz_publish.py` 是发布环节的核心：

### GitHub 发布
- 自动**分类**到 mswnlz 仓库（book / movies / AIknowledge / curriculum / tools 等）
- 分类策略：分辨率词(4K/蓝光) → movies；书籍词 → book；兜底按仓库描述评分
- 追加到 `YYYYMM.md`，更新 `README.md` 月份索引
- commit + push（SSH 认证）

### Telegram 通知
- 发送到多个群组（可配置 thread/topic）
- 统一一条消息，包含所有新增资源
- 多链接资源（夸克+百度）在同一消息中展示

### 站点重建
- 触发 `mswnlz.github.io` 仓库的空 commit + push
- GitHub Pages 自动重建

### 分类规则

| 信号 | 归类 |
|------|------|
| 4K / 蓝光 / 超清 / 1080P / 全N集 / 第N集 | movies |
| .mp4 / .mkv / .avi 等视频后缀 | movies |
| 书 / 书单 / 电子书 / 杂志 / N册 | book |
| 以上都不匹配 | 按仓库描述评分兜底（默认 curriculum） |

---

## 🔧 配置

### secrets.env

路径：`QuarkPanTool/config/secrets.env`

```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...     # TG Bot Token
GITHUB_TOKEN=ghp_xxx                      # GitHub Token（mswnlz 账户）
TELEGRAM_CHANNEL_ID=@dabaziyuan           # TG 频道

TG_GROUP_1_ID=-100xxxxxxxx                # 群组1 ID
TG_GROUP_1_THREAD=5                       # 群组1 话题 ID
TG_GROUP_2_ID=-100xxxxxxxx                # 群组2 ID
TG_GROUP_2_THREAD=2                       # 群组2 话题 ID
TG_GROUP_3_ID=                            # 群组3（可选）
TG_GROUP_3_THREAD=
TG_GROUP_4_ID=-100xxxxxxxx                # 群组4 ID
TG_GROUP_4_THREAD=235                     # 群组4 话题 ID
```

### items.json

路径：`scripts/items.json`（每次执行前更新）

```json
[
  {
    "title": "资源名称",
    "urls": ["https://pan.quark.cn/s/xxx"]
  }
]
```

支持 `url`（单个）和 `urls`（数组）两种格式，可混用。

---

## 📊 全流程数据流

```
items.json
    │
    ├──→ quark_batch_run.py ──→ batch_share_results_quark.json ──┐
    ├──→ baidu_batch_run.py ──→ batch_share_results_baidu.json ──┤
    └──→ aliyun_batch_run.py ──→ batch_share_results_aliyun.json ┤
                                                                 │
                    pipeline_orchestrator.py                     │
                    (merge_results 按资源名合并)  ←───────────────┘
                              │
                              ▼
                    batch_share_results.json
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     cleanup_junk     copy_promo      mswnlz_publish
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
| pipeline_orchestrator.py | 1.2.0 | 统一编排器，分流+合并+全流程串联 |
| quark_batch_run.py | 2.1.0 | 夸克转存+分享，集成多账号轮换 |
| quark_account_rotator.py | 1.0.0 | 多账号轮换器（独立可复用） |
| copy_promo_to_folders.py | 2.1.1 | 推广文件复制，动态发现 fid |
| mswnlz_publish.py | 1.0.0 | GitHub 发布 + TG 通知 + 站点重建 |
| cleanup_junk_files.py | 1.0.0 | 垃圾文件清理（夸克/百度/阿里云） |
| url_router.py | 1.1.0 | 网盘链接类型路由 |

---

## 📜 更新日志

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
- 重构为多网盘统一编排架构
- 新增阿里云盘支持
- 新增垃圾文件清理
- pipeline_orchestrator 支持 dry-run 模式

### v1.0.0 (2026-03-31)
- 初始版本
- 支持夸克网盘转存 + 分享 + GitHub 发布 + TG 通知
