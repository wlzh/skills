# WeSpy Fetcher Skill

> 仓库地址: https://github.com/wlzh/skills
> 版本: v1.1.0

把 [tianchangNorth/WeSpy](https://github.com/tianchangNorth/WeSpy) 封装成可直接调用的 Skill，支持微信公众号文章抓取、专辑批量下载、URL 转 Markdown 等完整能力。

## 依赖上游封装来源

- 上游项目：`https://github.com/tianchangNorth/WeSpy`
- 本 Skill 依赖上游项目的能力，并保持参数和行为尽量一致。

## 功能特性

- ✅ 抓取微信公众号单篇文章
- ✅ 抓取通用网页文章
- ✅ 支持掘金文章提取（上游已支持）
- ✅ 微信专辑列表获取（`--album-only`）
- ✅ 微信专辑批量下载（`--max-articles`）
- ✅ Markdown 默认输出
- ✅ 可选 HTML / JSON / 全格式输出（`--html` / `--json` / `--all`）
- ✅ 兼容上游交互模式（不传 URL）

## 目录约定（重要）

统一克隆目录：

- `~/Documents/QNSZ/project`

当前上游仓库实际路径：

- `~/Documents/QNSZ/project/WeSpy`

后续其他 topic 需要 `git clone` 的项目，也统一放在这个目录下。

## 快速开始

```bash
# 查看帮助
python3 scripts/wespy_cli.py --help

# 公众号文章转 Markdown
python3 scripts/wespy_cli.py "https://mp.weixin.qq.com/s/xxxxx"

# 专辑批量下载
python3 scripts/wespy_cli.py "https://mp.weixin.qq.com/mp/appmsgalbum?__biz=...&album_id=..." --max-articles 10 --all
```

## 依赖

- Python 3.8+
- git
- requests
- beautifulsoup4

可安装：

```bash
pip3 install -r scripts/requirements.txt
```

## 脚本说明

- `scripts/wespy_cli.py`
  - 自动检查上游源码是否存在
  - 缺失时自动 clone 到 `~/Documents/QNSZ/project/WeSpy`
  - 直接调用上游 `wespy.main.main`，确保能力齐全

## 致谢

感谢上游项目作者：

- https://github.com/tianchangNorth/WeSpy
