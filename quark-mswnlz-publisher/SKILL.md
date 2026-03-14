---
name: quark-mswnlz-publisher
description: "Automate the full QuarkPanTool → mswnlz GitHub content publishing pipeline. Use when the user provides Quark share URLs and wants: (1) create a batch folder in Quark Drive, (2) save/copy resources into that folder, (3) copy promotional files from template folder to each shared folder, (4) generate permanent encrypted share links with random passcodes, (5) auto-classify items into mswnlz repos (book/movies/etc.) by repo descriptions, (6) append/update the target repo's YYYYMM.md and README month index, (7) git commit+push, (8) send unified Telegram notifications, and (9) force-trigger mswnlz.github.io site rebuild and return the final site URLs."
---

# quark-mswnlz-publisher

**版本**: v1.2.0

夸克网盘 → mswnlz GitHub 资源仓库 → 站点自动更新，一条龙发布。

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

## 完整工作流

### 0) 输入收集

需要用户提供：
- 夸克分享 URL 列表（每条可包含标题）
- 目标月份 `YYYYMM`（默认：当前月份）
- 批次标签（默认：`短裤哥批次`）

### 1) 确保夸克登录状态

- 检查 `QuarkPanTool/config/cookies.txt`
- 如果不存在或为空：运行 `python quark_login.py`
- 登录流程：自动打开 Chrome → 用户扫码 → Cookie 自动保存

### 2) 批量转存 + 生成分享链接

使用 `scripts/quark_batch_run.py`：
1. 在夸克根目录创建批次文件夹（格式：`YYYY-MM-DD_HHMM_<label>`）
2. 批量转存所有分享 URL 到该文件夹
3. 列出文件夹内所有项目
4. 为每个顶层项目生成分享链接：
   - `url_type=2`（加密）
   - `expired_type=1`（永久）
   - 随机提取码
5. 输出 JSON：`batch_share_results.json`

### 3) 复制推广文件到每个文件夹 🆕

使用 `scripts/quark_copy.py`：
- 从夸克网盘的 `temp/要共享的文件` 文件夹复制推广文件
- 自动复制到每个转存的文件夹

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
2. 根据标题关键词归类：
   - 影视/电影/剧/纪录片/演唱会 → `movies`
   - 书/书单/新书/杂志/电子书/合集 → `book`
   - 其他：根据仓库 description 关键词匹配
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

## Telegram 通知机制

### 频道通知（@dabaziyuan）
- **每条资源单独发送**
- 包含：资源名称 + GitHub 链接
- 由 GitHub Workflow 自动触发

### 群组通知（tgmShare 话题5、tgmShareAI 话题2）
- **批量更新只发一条汇总消息**
- 包含：已更新仓库列表 + 资源数量 + 频道链接
- 由 Skills 脚本统一发送，避免刷屏

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

### scripts/quark_copy.py 🆕

从模板文件夹复制推广文件到目标文件夹。

```python
from quark_copy import add_promo_files_to_folder

# 复制推广文件到指定文件夹
await add_promo_files_to_folder(cookies, headers, target_folder_fid)
```

**前提条件**：
- 夸克网盘中存在 `temp/要共享的文件` 文件夹
- 该文件夹中包含推广文件

### scripts/mswnlz_publish.py

发布到 GitHub 仓库 + 发送 Telegram 群组通知。

```bash
python scripts/mswnlz_publish.py \
  --month 202603 \
  --batch-json batch_share_results.json
```

**依赖**：
- Git SSH 配置
- 可选：`GITHUB_TOKEN` 环境变量

### scripts/trigger_site_rebuild.sh

触发站点重建。

```bash
bash scripts/trigger_site_rebuild.sh
```

**依赖**：
- Git SSH 配置
- `mswnlz.github.io` 仓库写权限

## 推广文件

### 模板文件夹位置

夸克网盘：`temp/要共享的文件`

### 文件清单

| 文件名 | 用途 |
|--------|------|
| `必看免责声明_及加入资源分享群_及_副业_0_成本赚钱教程_资源网站doc_869hr_uk.txt` | 免责声明 + 联系方式 + 赚钱教程 |
| `1_解压密码869hr_uk_移动端双击这里.html` | 移动端解压密码获取页面 |
| `0_双击获取解压密码_Mac系统双击这里.webloc` | Mac 快捷方式 |
| `0_双击获取解压密码_windows系统双击这里.url` | Windows 快捷方式 |

### 本地备份

`promo_files/` 目录保存了推广文件的本地备份，用于参考和恢复。

## 详细文档

完整配置、依赖安装、故障排除请参阅 [README.md](README.md)。
