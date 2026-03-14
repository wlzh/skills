# quark-mswnlz-publisher

**版本**: v1.0.0

夸克网盘 → mswnlz GitHub 资源仓库 → 站点自动更新，一条龙发布。

## 功能

- **夸克批量转存**：新建批次文件夹 → 批量转存 URL
- **自动生成分享链接**：永久 + 加密 + 随机提取码
- **自动归类**：根据 mswnlz 仓库 description 判断写入 book/movies 等仓库
- **自动落盘**：追加/新建 `YYYYMM.md` + 更新 README 月份索引
- **自动提交**：commit（无链接，一条一行）+ push
- **强制触发站点构建**：`mswnlz.github.io` 站点构建（push 触发）并返回 Actions 链接/站点 URL

## 依赖

- Python 3.10+ (httpx, retrying, prettytable, tqdm, colorama)
- Playwright (仅用于 quark_login.py，需 `playwright install chromium`)
- Git (SSH 配置好可访问 mswnlz 仓库)
- 本地已存在 `/Users/m./Documents/QNSZ/project/QuarkPanTool` 仓库

## 使用方法

### 1. 准备输入文件

创建 `items.json`：

```json
[
  {"title": "2025年杂志合集", "url": "https://pan.quark.cn/s/xxx"},
  {"title": "大明王朝1566", "url": "https://pan.quark.cn/s/yyy"}
]
```

### 2. 确保夸克登录状态

```bash
cd /Users/m./Documents/QNSZ/project/QuarkPanTool
. .venv/bin/activate
python quark_login.py  # 首次需要
```

### 3. 批量转存 + 生成分享链接

```bash
python /Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/scripts/quark_batch_run.py \
  --label "短裤哥批次" \
  --month 202603 \
  --items-json items.json \
  --out-json batch_share_results.json
```

### 4. 发布到 GitHub 仓库

```bash
python /Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/scripts/mswnlz_publish.py \
  --month 202603 \
  --batch-json batch_share_results.json
```

### 5. 触发站点重建

```bash
bash /Users/m./Documents/QNSZ/project/skills/quark-mswnlz-publisher/scripts/trigger_site_rebuild.sh
```

## 归类规则

根据标题关键词自动归类：

- 包含 `影视`/`电影`/`剧`/`纪录片`/`演唱会` → `movies`
- 包含 `书`/`书单`/`新书`/`杂志`/`电子书`/`合集` → `book`
- 其他：根据 mswnlz 仓库 description 关键词匹配

## 输出格式

### YYYYMM.md 示例

```markdown
- 2025年杂志合集-超过100T资料总站网站-doc.869hr.uk | https://pan.quark.cn/s/xxx?pwd=abc1
- 大明王朝1566-超过100T资料总站网站-doc.869hr.uk | https://pan.quark.cn/s/yyy?pwd=abc2
```

### commit message 示例

```
增加 2025年杂志合集
增加 大明王朝1566
```

## 安全提示

- 不要在聊天中粘贴 GitHub Token
- 优先使用 SSH 方式访问 GitHub 仓库
- 如需 API 调用，通过环境变量 `GITHUB_TOKEN` 传入
