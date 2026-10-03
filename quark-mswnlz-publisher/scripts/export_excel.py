#!/usr/bin/env python3
"""export_excel.py — 把资源站 catalog 导出成可直接分享的 Excel 总表

输出三个工作表：
  1. 全部资源    一行一条，按分类分解成夸克/百度/阿里云三列，带详情页链接
  2. 分类汇总    每个分类的资源数与站点入口
  3. 关于与加群  站点简介、免责声明、各平台群组信息

用法：
    python3 export_excel.py                       # 输出到项目下的 export/ 目录
    python3 export_excel.py --out 资源总表.xlsx
    python3 export_excel.py --catalog /path/to/resource-catalog.json

Version: 1.0.0
"""

import argparse
import json
import re
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

SITE = "https://doc.869hr.uk"
BLOG = "https://869hr.uk"

# ── 样式 ──
HEAD_FILL = PatternFill("solid", fgColor="1F3864")
HEAD_FONT = Font(color="FFFFFF", bold=True, size=11)
TITLE_FONT = Font(bold=True, size=14, color="1F3864")
SUB_FONT = Font(size=11, bold=True, color="C00000")
LINK_FONT = Font(color="0563C1", underline="single", size=10)
CELL_FONT = Font(size=10)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
ALT_FILL = PatternFill("solid", fgColor="F2F5FA")

PROVIDER_COLUMNS = [
    ("夸克网盘", "quark"),
    ("百度网盘", "baidu"),
    ("阿里云盘", "aliyun"),
    ("其他链接", "other"),   # 短链（s.869hr.uk）等非标准网盘地址，不能丢
]

# 分类中文名兜底（catalog 里无该分类资源时也要显示名称）
CATEGORY_NAMES = {
    "AIknowledge": "AI 知识", "book": "书籍资料", "curriculum": "课程资料",
    "edu-knowlege": "教育资源", "movies": "影视娱乐", "tools": "工具合集",
    "self-media": "自媒体运营", "cross-border": "跨境电商", "healthy": "健康养生",
    "chinese-traditional": "传统文化", "auto": "自动化工具",
}

CATEGORY_ORDER = [
    "AIknowledge", "book", "curriculum", "edu-knowlege", "movies",
    "tools", "self-media", "cross-border", "healthy",
    "chinese-traditional", "auto",
]

# 站点/群组信息（取自项目内 about.md、profile README 与推广说明文件）
ABOUT_ROWS = [
    ("", ""),
    ("站点简介", "超过 100T 免费资源汇总，覆盖 AI、书籍、课程、影视、工具等 11 个分类，"
                 "每条资源有独立详情页，持续更新。"),
    ("资源总站", SITE),
    ("博客", BLOG),
    ("YouTube", "https://youtube.com/@gxjdian"),
    ("联系邮箱", "gxjdian@gmail.com"),
    ("", ""),
    ("【加入我们】", ""),
    ("Telegram 频道", "https://t.me/dabaziyuan"),
    ("Telegram 群", "https://t.me/tgmShareAI"),
    ("Telegram 群（备用）", "https://t.me/tgmknow   或加 Telegram ID：gxjdian"),
    ("微信群", "https://qr.869hr.uk/resource   或加微信 ID：gxjdian"),
    ("QQ 群", "1041415822（入群验证密码：869hr.uk）"),
    ("QQ 群（备用）", "1078469298"),
    ("夸克资源群", "打开夸克 App，输入夸克群号：2122364648"),
    ("百度资源群", "打开百度 App，输入百度群号：963783861"),
    ("", ""),
    ("【免责声明】", ""),
    ("说明", "本站所有资源均收集自互联网，仅供学习交流使用，不用于商业用途。"
             "资源版权归原作者所有，请于下载后 24 小时内删除并支持正版。"),
    ("侵权处理", "如涉及侵权，请通过邮箱 gxjdian@gmail.com 联系我们删除。"),
]


def load_catalog(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else (data.get("resources") or data.get("items") or [])
    return items


def split_pwd(url: str):
    """百度/阿里云盘链接里的提取码单独拆出来，便于用户复制"""
    m = re.search(r'[?&]pwd=([A-Za-z0-9]{4})', url or '')
    if m:
        return re.sub(r'[?&]pwd=[A-Za-z0-9]{4}', '', url), m.group(1)
    return url, ''


def provider_key(url: str) -> str:
    u = (url or "").lower()
    if "quark.cn" in u:
        return "quark"
    if "baidu.com" in u:
        return "baidu"
    if "aliyundrive" in u or "aliyunpan" in u:
        return "aliyun"
    return "other"


def build_workbook(items, out_path: Path):
    wb = Workbook()

    # ───────── Sheet 1: 全部资源 ─────────
    ws = wb.active
    ws.title = "全部资源"
    headers = ["序号", "分类", "所属月份", "资源名称"] + [c[0] for c in PROVIDER_COLUMNS] + ["提取码", "详情页"]
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER
    ws.freeze_panes = "A2"

    ordered = sorted(
        items,
        key=lambda it: (CATEGORY_ORDER.index(it["category"]) if it.get("category") in CATEGORY_ORDER else 99,
                        it.get("month", ""), it.get("title", "")),
    )

    for idx, it in enumerate(ordered, start=1):
        urls = [it.get("url", "")] + [u.get("url", "") for u in (it.get("altUrls") or [])]
        buckets, pwd = {}, ""
        for u in urls:
            if not u:
                continue
            clean, p = split_pwd(u)
            if p and not pwd:
                pwd = p
            buckets.setdefault(provider_key(u), clean)

        row = [
            idx,
            it.get("categoryName") or it.get("category", ""),
            it.get("month", ""),
            it.get("title", ""),
        ]
        row += [buckets.get(key, "") for _, key in PROVIDER_COLUMNS]
        row += [pwd, f"{SITE}/r/{it.get('id')}"]
        ws.append(row)

        r = ws.max_row
        shade = idx % 2 == 0
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = CELL_FONT
            cell.border = BORDER
            cell.alignment = Alignment(vertical="center", wrap_text=(c == 4))
            if shade:
                cell.fill = ALT_FILL
        # 网盘链接与详情页做成可点击超链接（最后两列是提取码与详情页，跳过）
        for c in range(5, 5 + len(PROVIDER_COLUMNS)):
            v = ws.cell(row=r, column=c).value
            if v:
                ws.cell(row=r, column=c).hyperlink = v
                ws.cell(row=r, column=c).font = LINK_FONT

    widths = [6, 14, 10, 52, 32, 32, 32, 32, 9, 38]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"

    # ───────── Sheet 2: 分类汇总 ─────────
    ws2 = wb.create_sheet("分类汇总")
    ws2.append(["分类", "分类名称", "资源数", "站点入口"])
    for c in range(1, 5):
        cell = ws2.cell(row=1, column=c)
        cell.fill, cell.font = HEAD_FILL, HEAD_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER

    from collections import Counter
    counter = Counter(it.get("category", "") for it in items)
    name_map = {it.get("category", ""): it.get("categoryName", "") for it in items}
    name_map.update(CATEGORY_NAMES)
    # 即使某分类当前无资源也要列出，避免分类总览缺项
    all_cats = set(counter) | set(CATEGORY_ORDER)
    for cat in sorted(all_cats, key=lambda k: CATEGORY_ORDER.index(k) if k in CATEGORY_ORDER else 99):
        url = f"{SITE}/{cat}/"
        ws2.append([cat, name_map.get(cat, ""), counter[cat], url])
        r = ws2.max_row
        for c in range(1, 5):
            ws2.cell(row=r, column=c).border = BORDER
            ws2.cell(row=r, column=c).font = CELL_FONT
        ws2.cell(row=r, column=4).hyperlink = url
        ws2.cell(row=r, column=4).font = LINK_FONT
    ws2.append([])
    ws2.append(["合计", "", len(items), SITE])
    r = ws2.max_row
    for c in range(1, 5):
        ws2.cell(row=r, column=c).font = Font(bold=True, size=10)
    for i, w in enumerate([18, 16, 10, 44], start=1):
        ws2.column_dimensions[get_column_letter(i)].width = w
    ws2.freeze_panes = "A2"

    # ───────── Sheet 3: 关于与加群 ─────────
    ws3 = wb.create_sheet("关于与加群")
    ws3["A1"] = "大坝的资源收集站 · 资源总表"
    ws3["A1"].font = TITLE_FONT
    ws3["A2"] = f"导出日期：{date.today().isoformat()}　|　共 {len(items)} 条资源"
    ws3["A2"].font = Font(size=10, color="666666")

    row = 4
    for label, value in ABOUT_ROWS:
        if label.startswith("【"):
            ws3.cell(row=row, column=1, value=label).font = SUB_FONT
        else:
            ws3.cell(row=row, column=1, value=label).font = Font(bold=True, size=10)
            cell = ws3.cell(row=row, column=2, value=value)
            cell.font = CELL_FONT
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if isinstance(value, str) and value.startswith("http") and " " not in value:
                cell.hyperlink = value
                cell.font = LINK_FONT
        row += 1
    ws3.column_dimensions["A"].width = 22
    ws3.column_dimensions["B"].width = 76

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return len(items)


def main():
    default_catalog = Path("/Users/m/document/QNSZ/project/mswnlz-github/mswnlz.github.io/docs/public/resource-catalog.json")
    ap = argparse.ArgumentParser(description="资源站 catalog → Excel 总表")
    ap.add_argument("--catalog", default=str(default_catalog), help="resource-catalog.json 路径")
    ap.add_argument("--out", default="", help="输出 xlsx 路径（缺省按日期命名）")
    args = ap.parse_args()

    catalog = Path(args.catalog)
    if not catalog.exists():
        raise SystemExit(f"catalog 不存在: {catalog}\n（先跑一次 npm run build 生成）")

    out = Path(args.out) if args.out else Path(
        "/Users/m/document/QNSZ/project/mswnlz-export") / f"资源总表-{date.today():%Y%m%d}.xlsx"

    n = build_workbook(load_catalog(catalog), out)
    print(f"已导出 {n} 条资源 → {out}")
    print(f"大小: {out.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
