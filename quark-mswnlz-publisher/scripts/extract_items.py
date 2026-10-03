#!/usr/bin/env python3
"""extract_items.py — 把「原始粘贴文本」转成 pipeline 可直接消费的 items.json

补的是 url_router.py 之前的缺口：url_router 只判断网盘类型，这里负责
把群消息/手工整理的文本解析成 {title, urls[]} 结构。

支持的文本写法（同一份文本里可混用）：
    1. 标题行 + 链接行         「XXX」\n链接：https://pan.quark.cn/s/xxx
    2. 标题行 + 裸链接         XXX\nhttps://pan.quark.cn/s/xxx
    3. 管道行                  XXX | https://pan.quark.cn/s/xxx
    4. Markdown 链接           [XXX](https://pan.quark.cn/s/xxx)
    5. 带 🔗 等前缀的链接行    🔗https://pan.quark.cn/s/xxx

用法：
    python3 extract_items.py --input raw.txt --out-json items.json
    cat raw.txt | python3 extract_items.py --out-json items.json

    # 可选：查夸克分享 API 取真实标题（默认关闭；网络请求，需代理）
    python3 extract_items.py --input raw.txt --out-json items.json --quark-titles

Version: 1.0.0
"""

import argparse
import json
import re
import sys
from pathlib import Path

from url_router import route_url

# 网盘分享链接（含不带协议的裸写法）。?query 要保留（百度提取码在 query 里），
# #fragment 会被一起吃掉（夸克链接常带 #/list/share 这类片段，不该进标题）。
URL_RE = re.compile(
    r'(?:https?://)?(?:'
    r'pan\.quark\.cn/s/[A-Za-z0-9]+'
    r'|pan\.baidu\.com/s/[\w\-]+|yun\.baidu\.com/s/[\w\-]+'
    r'|(?:www\.)?(?:aliyundrive|aliyunpan)\.com/s/[\w\-]+'
    r')(?:[?#][^\s)】\]]*)?'
)

# 链接行前缀：链接：/ 🔗 / 链接:
LINK_PREFIX_RE = re.compile(r'^(?:🔗|链接[：:]|地址[：:]|URL[：:]?)\s*', re.IGNORECASE)
MD_LINK_RE = re.compile(r'\[([^\]\n]+)\]\(((?:https?://)?(?:pan\.quark\.cn|pan\.baidu\.com|yun\.baidu\.com|(?:www\.)?(?:aliyundrive|aliyunpan)\.com)[^)\s]*)\)')

# 标题行常见包裹符号：「」《》【】"" 及结尾的说明
TITLE_TRIM_RE = re.compile(r'^[\s「『【《"\'·•\-\*]+|[\s」』】》"\'·•]+$')


def normalize_url(raw: str) -> str:
    """补全协议、去掉 #fragment 与尾部中文标点（保留 ?pwd= 提取码）"""
    url = raw.strip().rstrip('，。；、,.;)]}】')
    url = url.split('#', 1)[0]
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    return url


def clean_title(raw: str) -> str:
    title = TITLE_TRIM_RE.sub('', (raw or '').strip())
    title = re.sub(r'\s+', ' ', title)
    return title.strip()


def is_supported(url: str) -> bool:
    try:
        route_url(url)
        return True
    except ValueError:
        return False


def extract_items(text: str):
    """按行状态机解析：跟踪最近一个非链接行作为标题，遇到链接行时配对。"""
    items = []
    pending_title = None   # 仅用于「标题行 + 链接行」的配对
    last_title = ''        # 粘性标题：同一标题下的第 2..N 条裸链接也归它

    for raw_line in text.split('\n'):
        line = raw_line.strip()
        if not line:
            continue

        # 整行就是 markdown 链接：[标题](url)
        md = MD_LINK_RE.match(line)
        if md:
            title, url = clean_title(md.group(1)), normalize_url(md.group(2))
            if is_supported(url):
                items.append({'title': title, 'url': url})
            continue

        # 管道行：标题 | url
        if '|' in line:
            left, _, right = line.partition('|')
            found = URL_RE.findall(right)
            if found:
                title = clean_title(left) or clean_title(right.replace(found[0], ''))
                for f in found:
                    url = normalize_url(f)
                    if is_supported(url):
                        items.append({'title': title, 'url': url})
                pending_title = None
                continue

        # 行内含链接（可能一行多条，或带 🔗/链接：前缀）
        found = URL_RE.findall(line)
        if found:
            # 去掉链接后行内残留的文字才可能作标题；残留若是 URL 片段（#/list/share）
            # 或以标点开头，说明这行本就是裸链接行，标题应沿用上一行的标题。
            remainder = line
            for f in found:
                remainder = remainder.replace(f, ' ')
            inline_title = clean_title(LINK_PREFIX_RE.sub('', remainder))
            if not inline_title or inline_title.startswith(('#', '/', '?', '#')):
                inline_title = ''
            title = inline_title or pending_title or last_title
            for f in found:
                url = normalize_url(f)
                if not is_supported(url):
                    continue
                items.append({'title': title, 'url': url})
            pending_title = None
            if title:
                last_title = title
            continue

        # 普通文字行 → 暂存为待配对标题
        pending_title = clean_title(line)
        if pending_title:
            last_title = pending_title

    # 同一标题的多条链接合并成 urls[]
    merged, index = [], {}
    for it in items:
        key = it['title']
        if key and key in index:
            index[key]['urls'].append(it['url'])
        else:
            rec = {'title': it['title'], 'urls': [it['url']]}
            index[key] = rec
            merged.append(rec)

    # 去重链接
    for rec in merged:
        seen, uniq = set(), []
        for u in rec['urls']:
            if u not in seen:
                seen.add(u)
                uniq.append(u)
        rec['urls'] = uniq

    # 单链接回退成 url 字段（兼容 pipeline 的旧格式）
    for rec in merged:
        if len(rec['urls']) == 1:
            rec['url'] = rec['urls'][0]
            del rec['urls']

    return merged


def fetch_quark_titles(items, proxy: str = None):
    """用夸克分享 API 取真实标题（分享页是 JS 渲染的，拿不到 <title>）。"""
    import urllib.request

    handlers = [urllib.request.ProxyHandler({'http': proxy, 'https': proxy})] if proxy else []
    opener = urllib.request.build_opener(*handlers)
    fixed = 0
    for rec in items:
        urls = rec.get('urls') or ([rec['url']] if rec.get('url') else [])
        for u in urls:
            m = re.search(r'pan\.quark\.cn/s/([A-Za-z0-9]+)', u)
            if not m:
                continue
            try:
                req = urllib.request.Request(
                    'https://pan.quark.cn/1/clouddrive/share/sharepage/token?pr=ucpro&fr=pc',
                    data=json.dumps({'pwd_id': m.group(1), 'passcode': ''}).encode(),
                    headers={'Content-Type': 'application/json',
                             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                                           'AppleWebKit/537.36 Chrome/120 Safari/537.36'})
                with opener.open(req, timeout=25) as r:
                    title = ((json.load(r).get('data') or {}).get('title') or '').strip()
                if title and title != rec.get('title'):
                    rec['original_title'] = rec.get('title', '')
                    rec['title'] = title
                    fixed += 1
                break
            except Exception:
                continue
    return fixed


def main():
    ap = argparse.ArgumentParser(description='原始文本 → items.json')
    ap.add_argument('--input', help='输入文本文件（缺省从 stdin 读）')
    ap.add_argument('--out-json', default='items.json', help='输出 JSON 路径（默认 items.json）')
    ap.add_argument('--quark-titles', action='store_true',
                    help='查夸克分享 API 取真实标题覆盖解析出的标题（需网络，可配 --proxy）')
    ap.add_argument('--proxy', default='http://127.0.0.1:7798', help='--quark-titles 用的代理')
    args = ap.parse_args()

    text = Path(args.input).read_text(encoding='utf-8') if args.input else sys.stdin.read()
    items = extract_items(text)

    if args.quark_titles and items:
        fixed = fetch_quark_titles(items, args.proxy)
        print(f'[titles] 用夸克 API 修正了 {fixed} 条标题', file=sys.stderr)

    out = Path(args.out_json)
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'解析出 {len(items)} 条资源 → {out}')
    for it in items[:5]:
        n = len(it.get('urls', [it.get('url', '')]))
        print(f"  {it['title'][:44] or '(无标题)'}  [{n} 个链接]")
    if len(items) > 5:
        print(f'  …… 其余 {len(items) - 5} 条见 {out}')


if __name__ == '__main__':
    main()
