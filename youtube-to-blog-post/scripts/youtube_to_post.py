#!/usr/bin/env python3
"""
YouTube to Blog Post Script - SEO Optimized Version
Convert YouTube videos to Hexo blog posts with enhanced SEO
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
import subprocess
import shutil

try:
    import yt_dlp
except ImportError:
    print("Installing yt-dlp...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp


# SEO optimization constants
MAX_DESCRIPTION_LENGTH = 160  # Google SEO recommended
MAX_KEYWORDS = 8  # Optimal number for SEO
MIN_KEYWORD_LENGTH = 2
MAX_KEYWORD_LENGTH = 20
MAX_FILENAME_LENGTH = 50  # Short, readable URLs perform better

# Stop words to filter from keywords
STOP_WORDS = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', 'https', 'http', 'www', 'com', 'cn', 'org', 'net', '://', '//',
    '加入', '这个', '那个', '可以', '使用', '通过', '进行', '如果', '因为', '所以',
}

# Common tech keyword mappings for better SEO
KEYWORD_SYNONYMS = {
    'ai': ['AI', '人工智能', 'artificial intelligence'],
    'vps': ['VPS', '虚拟服务器', 'virtual private server'],
    'cdn': ['CDN', '内容分发网络', 'content delivery network'],
    'ssl': ['SSL', 'HTTPS', '安全证书'],
    '域名': ['domain', '域名注册'],
    '服务器': ['server', '主机'],
    '免费': ['free', '0成本', '免费资源'],
    '教程': ['tutorial', '指南', 'guide', 'how to'],
}

# Standard tag taxonomy (v3.2) - must be used when generating tags
STANDARD_TAGS = {
    'AI': ['AI', '人工智能', 'AGI', 'ai'],
    'AI工具': ['AI工具', 'ai工具', 'ai tools'],
    'AI前沿': ['AI前沿', 'ai前沿', 'AI frontier'],
    'LLM': ['LLM', '大语言模型', 'llm'],
    'DeepSeek': ['DeepSeek', 'deepseek'],
    'ChatGPT': ['ChatGPT', 'chatgpt', 'GPT'],
    'Claude': ['Claude'],
    'Skills': ['Skills', 'skills'],
    '跨境支付': ['跨境支付', '支付', '出海收款'],
    '信用卡': ['信用卡', '虚拟信用卡', 'credit card'],
    'Wise': ['Wise', 'wise'],
    'Stripe': ['Stripe', 'stripe'],
    '苹果支付': ['苹果支付', 'iOS支付', 'apple payment'],
    '加密货币': ['加密货币', 'crypto', '比特币', '币安'],
    'VPN': ['VPN', 'vpn', '梯子', '翻墙', '科学上网', 'v2ray'],
    'VPS': ['VPS', 'vps', '服务器', '云服务器'],
    'Cloudflare': ['Cloudflare', 'cloudflare', 'CF'],
    '网络工具': ['网络工具', 'network tools'],
    '网络安全': ['网络安全', 'network security'],
    'ip属性': ['ip属性', 'ip检查', 'IP属性'],
    'eSIM': ['eSIM', 'esim'],
    'Apple ID': ['Apple ID', 'apple id', '苹果账号', '美区账号'],
    'App Store': ['App Store', 'app store'],
    'iOS': ['iOS', 'ios'],
    '在线工具': ['在线工具', 'online tools'],
    '效率工具': ['效率工具', 'productivity', '自动化'],
    '开发工具': ['开发工具', 'dev tools', '开发者工具'],
    '开源项目': ['开源项目', 'open source', '开源工具'],
    '无需安装': ['无需安装', 'no installation'],
    '剪映': ['剪映', '剪影', '视频编辑'],
    '教程': ['教程', '技术教程', '小白教程', '新手教程'],
    '视频教程': ['视频教程', 'video tutorial'],
    '免费资源': ['免费资源', 'free resource', '白嫖'],
    '学习资源': ['学习资源', 'learning resource'],
    '知识分享': ['知识分享', 'knowledge sharing'],
    '播客推荐': ['播客推荐', 'podcast'],
    '网赚项目': ['网赚项目', 'online earning', '被动收入'],
    '账号注册': ['账号注册', '注册', 'account registration'],
    '账号管理': ['账号管理', 'account management'],
    '邮箱': ['邮箱', 'email', 'gmail'],
    '海外应用': ['海外应用', 'foreign apps'],
    '软件安装': ['软件安装', 'software install'],
    '软件汉化': ['软件汉化', 'i18n', '中文语言包'],
    '本地部署': ['本地部署', 'local deployment', '私有部署'],
    '域名': ['域名', 'domain', '免费域名'],
    '数据安全': ['数据安全', 'data security', '隐私保护', '加密'],
    '文件传输': ['文件传输', 'file transfer', 'PairDrop'],
    '跨平台工具': ['跨平台工具', 'cross platform'],
    '即时通讯': ['即时通讯', 'IM', '即时通信'],
    '社交软件': ['社交软件', 'social'],
    '微信': ['微信', 'wechat'],
    'Telegram': ['Telegram', 'telegram', 'tg'],
    'Google': ['Google', 'google', '谷歌'],
    '闲谈': ['闲谈', 'chat'],
    '技术交流': ['技术交流', 'tech community'],
    '技术支持': ['技术支持', 'tech support'],
    '客户支持': ['客户支持', 'customer support'],
    '故障处理': ['故障处理', 'troubleshooting'],
    '苹果': ['苹果', 'apple', 'iPhone'],
    '公司注册': ['公司注册', 'company registration'],
    '建站': ['建站', 'site building'],
    'SEO': ['SEO', '搜索引擎优化'],
}

def yaml_safe_string(value: str) -> str:
    """Wrap a string in double quotes and escape internal backslashes/quotes.

    Prevents YAML from misinterpreting *, [, ], {, }, &, !, |, >, % as
    YAML syntax tokens, aliases, anchors, or block scalars.
    """
    if not value:
        return '""'
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def normalize_tag(tag):
    """Normalize a tag to its standard form using the STANDARD_TAGS mapping."""
    tag_stripped = tag.strip()
    for standard, variants in STANDARD_TAGS.items():
        for v in variants:
            if tag_stripped.lower() == v.lower():
                return standard
    return tag_stripped


def load_config(config_path=None, blog_dir=None):
    """Load configuration from config file or use defaults"""
    config = {
        "posts_dir": "source/_posts",
        "default_category": "技术",
        "default_tags": ["视频教程"],
        "author": "M.",
        "image_cdn": "https://img.869hr.uk",
        "auto_deploy": False,
        "deploy_branch": "main"
    }

    # Priority 1: User's home directory config (for personal settings)
    home_config = os.path.expanduser("~/.youtube-blog-config.json")
    if os.path.exists(home_config):
        with open(home_config, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            config.update(user_config)

    # Priority 2: Explicit config path
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            config.update(user_config)
    # Priority 3: Blog directory config
    elif blog_dir:
        config_path = os.path.join(blog_dir, "youtube-blog-config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                config.update(user_config)

    return config


def sanitize_text_for_yaml(text):
    """
    Sanitize text for YAML format
    Remove or escape special characters that break YAML parsing
    """
    if not text:
        return text

    # Remove YAML special characters
    text = re.sub(r'[*&:!|>]', '', text)  # Remove problematic chars
    text = re.sub(r'[【】《》「」『』（）()]', '', text)  # Remove Chinese brackets
    text = re.sub(r'[\[\]{}]', '', text)  # Remove brackets
    text = text.strip()

    return text


def clean_keywords(keywords):
    """Clean and optimize keywords for SEO"""
    cleaned = []

    for kw in keywords:
        # Remove special characters
        kw = sanitize_text_for_yaml(kw)

        # Skip if too short or too long
        if len(kw) < MIN_KEYWORD_LENGTH or len(kw) > MAX_KEYWORD_LENGTH:
            continue

        # Skip stop words
        if kw.lower() in STOP_WORDS:
            continue

        # Skip URLs
        if kw.startswith(('http', 'https', 'www', '//')):
            continue

        # Skip if starts with special chars
        if re.match(r'^[^\w]', kw):
            continue

        cleaned.append(kw)

    return cleaned


def get_video_info(url):
    """Fetch video information from YouTube"""
    print(f"Fetching video info from: {url}")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                'id': info.get('id', ''),
                'title': sanitize_text_for_yaml(info.get('title', 'Untitled')),
                'description': info.get('description', ''),
                'uploader': info.get('uploader', ''),
                'upload_date': info.get('upload_date', ''),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'tags': info.get('tags', []),
                'view_count': info.get('view_count', 0),
            }
        except Exception as e:
            print(f"Error fetching video info: {e}")
            return None


def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def generate_english_filename(title, video_id=None):
    """Generate SEO-friendly English filename from video title"""
    # Phrase mapping is ordered by length so Chinese titles keep meaningful words
    # instead of turning into concatenated fragments.
    keyword_map = [
        # High-value phrases
        ('claude code', 'claude-code'),
        ('happy coder', 'happy-coder'),
        ('手机远程控制', 'mobile-remote-control'),
        ('远程控制', 'remote-control'),
        ('安装配置', 'install-config'),
        ('全教程', 'tutorial'),
        ('保姆级教程', 'step-by-step-tutorial'),
        ('小白教程', 'beginner-tutorial'),
        ('临时邮箱', 'temp-email'),
        ('域名邮箱', 'domain-email'),
        ('中转站', 'proxy-station'),
        ('开源项目', 'open-source'),
        ('自建中继', 'self-hosted-relay'),
        ('会话管理', 'session-management'),
        ('国内网络', 'china-network'),
        ('网络问题', 'network-issues'),
        ('全链路', 'end-to-end'),
        ('加密', 'encryption'),
        ('科学上网', 'vpn'),
        ('人工智能', 'ai'),
        ('机器学习', 'ml'),
        ('深度学习', 'deep-learning'),
        ('云计算', 'cloud'),
        ('容器化', 'docker'),
        # Common words
        ('教程', 'tutorial'),
        ('指南', 'guide'),
        ('工具', 'tools'),
        ('技术', 'tech'),
        ('免费', 'free'),
        ('域名', 'domain'),
        ('服务器', 'server'),
        ('支付', 'payment'),
        ('银行卡', 'bank-card'),
        ('虚拟', 'virtual'),
        ('注册', 'register'),
        ('申请', 'apply'),
        ('设置', 'setup'),
        ('配置', 'config'),
        ('开发', 'dev'),
        ('学习', 'study'),
        ('入门', 'beginner'),
        ('进阶', 'advanced'),
        ('详解', 'detail'),
        ('使用', 'usage'),
        ('安装', 'install'),
        ('部署', 'deploy'),
        ('测试', 'test'),
        ('优化', 'optimize'),
        ('分析', 'analysis'),
        ('介绍', 'intro'),
        ('什么是', 'what-is'),
        ('如何', 'how-to'),
        ('为什么', 'why'),
        ('最佳', 'best'),
        ('推荐', 'recommend'),
        ('对比', 'compare'),
        ('评测', 'review'),
        ('最新', ''),
        ('手机', 'mobile'),
        ('电脑', 'desktop'),
        ('远程', 'remote'),
        ('控制', 'control'),
        ('卡', 'card'),
    ]

    filename = title.lower()
    for cn, en in sorted(keyword_map, key=lambda item: len(item[0]), reverse=True):
        replacement = f" {en} " if en else " "
        filename = filename.replace(cn.lower(), replacement)

    # Normalize remaining punctuation/unknown characters into separators.
    filename = re.sub(r'[^\x00-\x7f]', '-', filename)
    filename = re.sub(r'[^a-z0-9]+', '-', filename)
    filename = re.sub(r'-{2,}', '-', filename).strip('-')
    tokens = [token for token in filename.split('-') if token]
    tokens = optimize_filename_tokens(tokens)
    filename = '-'.join(tokens)

    # If filename is too short or empty, use video ID
    if len(filename) < 5 or not filename:
        filename = f"youtube-{video_id}" if video_id else "video-post"

    # Limit length for SEO (shorter URLs are better)
    if len(filename) > MAX_FILENAME_LENGTH:
        filename = trim_filename(filename, MAX_FILENAME_LENGTH)

    return filename


def optimize_filename_tokens(tokens):
    """Keep filename tokens short, deduplicated, and keyword-first."""
    low_value = {
        '2023', '2024', '2025', '2026', 'latest', 'new', 'full', 'complete',
        'best', 'how', 'to', 'the', 'and', 'or',
    }
    filtered = []
    for token in tokens:
        if token in low_value:
            continue
        if token not in filtered:
            filtered.append(token)

    product_prefixes = [
        ['claude', 'code'],
        ['happy'],
        ['chatgpt'],
        ['openai'],
        ['cloudflare'],
        ['vps'],
        ['cpa'],
    ]

    prioritized = []
    remaining = filtered[:]
    for sequence in product_prefixes:
        if all(token in remaining for token in sequence):
            for token in sequence:
                if token not in prioritized:
                    prioritized.append(token)
                remaining.remove(token)

    if 'tutorial' in remaining:
        remaining.remove('tutorial')
        remaining.append('tutorial')

    tokens = prioritized + remaining

    removable = [
        'install', 'config', 'setup', 'usage', 'detail', 'intro', 'guide',
        'tech', 'tools', 'dev',
    ]
    while len('-'.join(tokens)) > MAX_FILENAME_LENGTH:
        removed = False
        for token in removable:
            if token in tokens and token not in {'tutorial'}:
                tokens.remove(token)
                removed = True
                break
        if not removed:
            break

    return tokens


def trim_filename(filename, max_length):
    """Trim without cutting a token; preserve trailing tutorial/guide when possible."""
    tokens = filename.split('-')
    if len(tokens) <= 1:
        return filename[:max_length].rstrip('-')

    ending = ''
    if tokens[-1] in {'tutorial', 'guide', 'review'}:
        ending = tokens.pop()

    while tokens and len('-'.join(tokens + ([ending] if ending else []))) > max_length:
        tokens.pop()

    if ending and ending not in tokens:
        tokens.append(ending)

    result = '-'.join(tokens).strip('-')
    return result or filename[:max_length].rstrip('-')


def generate_seo_keywords(title, description, tags):
    """
    Generate SEO-optimized keywords
    Focus on long-tail keywords and search intent
    """
    keywords = []

    def add_keyword(keyword):
        keyword = sanitize_text_for_yaml(keyword.strip())
        if not keyword:
            return
        if keyword.lower() in STOP_WORDS:
            return
        if keyword.startswith(('http', 'https', 'www', '//')):
            return
        if len(keyword) < MIN_KEYWORD_LENGTH or len(keyword) > MAX_KEYWORD_LENGTH:
            return
        if keyword not in keywords:
            keywords.append(keyword)

    for keyword in extract_semantic_keywords(title, description):
        add_keyword(keyword)

    # 1. Extract from title (highest priority)
    title_words = re.split(r'[\s,，、:：!！?？|｜/()\[\]【】《》「」『』]+', title)
    for word in title_words:
        add_keyword(word)

    # 2. Add user-provided tags
    if isinstance(tags, list):
        for tag in tags:
            add_keyword(tag)
    elif isinstance(tags, str):
        for tag in tags.split(','):
            add_keyword(tag)

    # 3. Extract high-value keywords from description
    if description:
        # Look for patterns like "关键词：xxx" or "关键词: xxx"
        keyword_pattern = r'关键词[：:]\s*([^\n]+)'
        keyword_matches = re.findall(keyword_pattern, description)
        for match in keyword_matches:
            kws = re.split(r'[,，、\s]+', match)
            for kw in kws:
                add_keyword(kw)

        # Extract meaningful phrases from description
        desc_sentences = re.split(r'[。！？.!?]', description)[:2]
        for sentence in desc_sentences:
            # Look for tech terms and product names
            tech_terms = re.findall(r'[A-Za-z][A-Za-z0-9+.-]*(?:\s+[A-Za-z][A-Za-z0-9+.-]*)?', sentence)
            for term in tech_terms:
                add_keyword(term)

    # Add related keywords for better SEO coverage
    final_keywords = []
    for kw in keywords:
        final_keywords.append(kw)

        # Add synonyms for important keywords
        if kw.lower() in KEYWORD_SYNONYMS:
            for synonym in KEYWORD_SYNONYMS[kw.lower()][:2]:
                if synonym not in final_keywords and len(final_keywords) < MAX_KEYWORDS:
                    final_keywords.append(synonym)

    return final_keywords[:MAX_KEYWORDS]


def extract_semantic_keywords(title, description=''):
    """Extract canonical search keywords before falling back to raw title tokens."""
    text = f"{title}\n{description}"
    text_lower = text.lower()
    keywords = []

    def add(keyword):
        if keyword not in keywords:
            keywords.append(keyword)

    # Topic-specific bundles prevent Chinese titles from turning into noisy fragments.
    if 'claude code' in text_lower and 'happy' in text_lower:
        for keyword in [
            'Claude Code',
            'Happy',
            '手机远程控制',
            'Happy安装配置',
            'Claude Code远程控制',
            '手机控制Claude Code',
            'E2EE加密',
            '远程开发',
            '小白教程',
        ]:
            add(keyword)

    if 'cloudflare' in text_lower and '邮箱' in text:
        for keyword in [
            'Cloudflare',
            'Cloudflare临时邮箱',
            '域名邮箱',
            '免费邮箱',
            'Workers',
            'D1数据库',
            'KV缓存',
            '小白教程',
        ]:
            add(keyword)

    phrase_keywords = [
        ('临时邮箱', '临时邮箱'),
        ('域名邮箱', '域名邮箱'),
        ('自建中继', '自建中继'),
        ('会话管理', '会话管理'),
        ('国内网络', '国内网络'),
        ('手机远程控制', '手机远程控制'),
        ('安装配置', '安装配置'),
        ('E2EE', 'E2EE加密'),
        ('Docker', 'Docker'),
        ('VPS', 'VPS'),
        ('CPA', 'CPA'),
        ('Codex', 'Codex'),
        ('OpenAI', 'OpenAI'),
        ('Cloudflare', 'Cloudflare'),
    ]
    for needle, keyword in phrase_keywords:
        if needle.lower() in text_lower:
            add(keyword)

    return keywords


def generate_seo_description(title, description):
    """
    Generate SEO-optimized description
    - Max 160 characters (Google snippet length)
    - Include main keywords
    - Compelling call-to-action
    """
    specialized_desc = generate_specialized_description(title)
    if specialized_desc:
        return specialized_desc[:MAX_DESCRIPTION_LENGTH]

    title_terms = extract_seo_terms(title)

    # Clean up description
    if description:
        # Remove URLs, email addresses
        desc = re.sub(r'https?://\S+', '', description)
        desc = re.sub(r'\S+@\S+', '', desc)

        # Remove excessive whitespace
        desc = re.sub(r'\s+', ' ', desc).strip()

        # Prefer the most keyword-rich sentence, not simply the first sentence.
        candidates = []
        sentences = re.split(r'[。！？.!?]', desc)
        for sentence in sentences:
            sentence = sentence.strip(' -，,；;：:')
            if len(sentence) < 20 or len(sentence) > MAX_DESCRIPTION_LENGTH:
                continue
            score = score_seo_sentence(sentence, title_terms)
            candidates.append((score, len(sentence), sentence))

        candidates = [item for item in candidates if item[0] > 0]
        if candidates:
            candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
            return candidates[0][2]

    # Fallback to title-based description
    desc_template = generate_title_based_description(title)
    if len(desc_template) > MAX_DESCRIPTION_LENGTH:
        desc_template = f"{title} - 详细教程与指南"

    return desc_template[:MAX_DESCRIPTION_LENGTH]


def generate_specialized_description(title):
    """Return high-quality descriptions for common tutorial categories."""
    if re.search(r'Claude Code', title, re.IGNORECASE) and re.search(r'Happy', title, re.IGNORECASE):
        return "Happy 安装配置教程：用手机远程控制 Claude Code，覆盖安装配对、会话管理、国内网络问题和自建中继。"

    if re.search(r'Cloudflare', title, re.IGNORECASE) and '邮箱' in title:
        return "Cloudflare 临时邮箱搭建教程，覆盖域名托管、邮件路由、D1、KV、Workers、Pages 部署和常见配置。"

    return ''


def extract_seo_terms(text):
    """Extract terms that should appear in SEO descriptions."""
    text_lower = text.lower()
    terms = set()

    ascii_terms = re.findall(r'[A-Za-z][A-Za-z0-9+.-]*(?:\s+[A-Za-z][A-Za-z0-9+.-]*)?', text)
    for term in ascii_terms:
        if len(term) >= 2:
            terms.add(term.lower())

    chinese_terms = [
        '手机远程控制', '远程控制', '安装配置', '安装', '配置', '教程',
        '自建中继', '会话管理', '国内网络', '网络问题', '加密',
        '临时邮箱', '域名邮箱', '免费', '部署', 'cloudflare',
        'vps', 'cpa', 'api', 'docker',
    ]
    for term in chinese_terms:
        if term.lower() in text_lower:
            terms.add(term.lower())

    return terms


def score_seo_sentence(sentence, terms):
    """Score sentences by how many title/search terms they contain."""
    sentence_lower = sentence.lower()
    score = 0
    for term in terms:
        if term and term in sentence_lower:
            score += 2 if len(term) > 4 else 1

    if re.search(r'教程|安装|配置|部署|指南|全流程|手把手', sentence):
        score += 1
    if re.search(r'http|关注|点赞|订阅|优惠码|推荐码', sentence_lower):
        score -= 2

    return score


def generate_title_based_description(title):
    """Build a concise fallback that still includes title keywords."""
    return f"{title}教程，整理核心步骤、配置方法、常见问题和参考链接。"


def generate_post_content(video_info, config, category, tags, body_md=""):
    """Generate SEO-optimized blog post content.

    When body_md is provided, it is already-formatted Markdown that bypasses
    format_description_as_markdown() — used when the upstream pipeline has
    already cleaned and formatted the blog source (e.g. duanku blog-source.md).
    """

    video_id = video_info['id']
    title = video_info['title']
    description = video_info.get('description', '')
    thumbnail = video_info.get('thumbnail', '')

    # Generate SEO-optimized metadata
    keywords = generate_seo_keywords(title, description, tags)
    post_description = generate_seo_description(title, description)

    # Use current time as post date (not video upload time)
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Generate tags list - normalize to standard tags
    raw_tags = tags if isinstance(tags, list) else [t.strip() for t in tags.split(',')]
    tag_list = []
    for t in raw_tags:
        normalized = normalize_tag(t)
        if normalized not in tag_list:
            tag_list.append(normalized)

    # Build cover image URL with 3-level fallback:
    # 1. Local custom thumbnail (if provided via --thumbnail arg)
    # 2. YouTube maxresdefault.jpg (if accessible)
    # 3. YouTube sddefault.jpg (always available fallback)
    local_thumbnail = config.get('local_thumbnail', '')
    maxres_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    sd_url = f"https://img.youtube.com/vi/{video_id}/sddefault.jpg"

    if local_thumbnail:
        cover_image = local_thumbnail
    else:
        try:
            import requests
            resp = requests.head(maxres_url, timeout=5, allow_redirects=True)
            cover_image = maxres_url if resp.status_code == 200 else sd_url
        except Exception:
            cover_image = sd_url

    # Build front matter with SEO fields
    front_matter = f"""---
title: {yaml_safe_string(title)}
subtitle: {yaml_safe_string(title)}
date: {date_str}
updated: {date_str}
author: {config['author']}
description: {yaml_safe_string(post_description)}
categories:
  - {category}
{generate_tags_yaml(tag_list)}
keywords:
{generate_keywords_yaml(keywords)}
cover: {cover_image}
thumbnail: {cover_image}
toc: true
comments: true
copyright: true
---

"""

    # Generate article summary
    summary = generate_article_summary(video_info)

    # Generate video iframe with responsive wrapper
    video_iframe = f"""## 视频教程

<div class="video-container"><iframe src="https://www.youtube.com/embed/{video_id}" title="{title.replace(chr(34), '&quot;')}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>

"""

    # Generate article content — use pre-formatted body if provided
    if body_md.strip():
        content = generate_article_content_with_body(video_info, video_id, body_md)
    else:
        content = generate_article_content(video_info, video_id)

    # Generate reference links
    references = f"""

## 参考链接

- [YouTube视频原地址](https://www.youtube.com/watch?v={video_id})
- [相关推荐](https://869hr.uk)

---
"""

    return front_matter + summary + video_iframe + content + references


def generate_tags_yaml(tags):
    """Generate tags in YAML format"""
    if not tags:
        return "tags:"
    yaml = "tags:\n"
    for tag in tags:
        yaml += f"  - {tag}\n"
    return yaml


def generate_keywords_yaml(keywords):
    """Generate keywords in YAML format"""
    if not keywords:
        return ""
    yaml = ""
    for kw in keywords:
        # Escape special YAML characters
        kw_safe = sanitize_text_for_yaml(kw)
        yaml += f"  - {kw_safe}\n"
    return yaml


def generate_article_summary(video_info):
    """Generate compelling article summary"""
    title = video_info['title']
    description = video_info.get('description', '')
    duration = video_info.get('duration', 0)

    # Convert duration to minutes
    duration_min = duration // 60 if duration else 0

    if description:
        # Use first meaningful paragraph from description
        lines = description.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 20:
                summary = line[:300]
                return f"""<!-- 文章摘要 -->
{{% blockquote %}}
{summary}...
{{% endblockquote %}}

"""
    return f"""<!-- 文章摘要 -->
{{% blockquote %}}
本视频详细介绍{title}（时长约{duration_min}分钟），帮助你快速了解和掌握相关知识点。
{{% endblockquote %}}

"""


def normalize_description_line(line):
    """Normalize a single YouTube description line without changing meaning."""
    line = line.strip()
    line = re.sub(r'\s+', ' ', line)
    line = line.replace('：：', '：')
    return line


def split_inline_items(text):
    """Split semicolon-heavy text into readable bullet items."""
    return [item.strip() for item in re.split(r'[；;]\s*', text) if item.strip()]


def add_heading(output, heading, current_heading):
    """Append a heading only when it changes."""
    if current_heading == heading:
        return current_heading
    if output and output[-1] != '':
        output.append('')
    output.extend([heading, ''])
    return heading


def format_resource_line(line):
    """Convert resource/promo lines into Markdown list or quote style."""
    if not line:
        return []

    line = normalize_description_line(line)

    if line.startswith('#') and ' ' not in line:
        return [line]

    if line.startswith('注意') and ('链接' in line or '复制' in line):
        cleaned = re.sub(r'[⚠️！!]+', '', line).strip()
        return [f"> {cleaned}"]

    if re.match(r'^\d+[.、]\s*', line):
        line = re.sub(r'^(\d+)[、]\s*', r'\1. ', line)
        return [line]

    if re.match(r'^[-*]\s+', line):
        return [line]

    if 'http' in line or 'www.' in line:
        return [f"- {line}"]

    return [line]


def format_colon_items(line):
    """Format lines like '三种情况：A；B；C' as a paragraph plus bullets."""
    match = re.match(r'^(.+?[：:])\s*(.+)$', line)
    if not match:
        return None

    lead, rest = match.groups()
    items = split_inline_items(rest)
    if len(items) < 2:
        return None

    formatted = [lead]
    for item in items:
        formatted.append(f"- {item}")
    return formatted


def description_heading_for_line(line):
    """Infer a useful section heading from common YouTube description patterns."""
    rules = [
        (r'^试了几种方案', '## 为什么普通远程方案不够顺手'),
        (r'^后来翻到', '## Happy 是什么'),
        (r'^简单说', '## 工作原理'),
        (r'^安装就一行', '## 安装与配对'),
        (r'^会话管理', '## 会话管理'),
        (r'^日常用法', '## 日常用法'),
        (r'^国内使用常见问题', '## 国内网络问题'),
        (r'^自建中继', '## 自建中继'),
        (r'^常见坑', '## 常见坑'),
        (r'^出门在外想改代码', '## 本期内容概览'),
        (r'^短信及语音接码平台', '## 短信及语音接码平台'),
        (r'^白嫖流量', '## 白嫖流量'),
        (r'^VPS\s*主机', '## VPS 主机推荐'),
        (r'^Gmail、Telegram', '## 账号、礼品卡与 AI 产品充值'),
        (r'^Claude、OpenAI', '## 账号、礼品卡与 AI 产品充值'),
        (r'^👇?【?关注我不迷路', '## 关注与资源'),
    ]

    for pattern, heading in rules:
        if re.search(pattern, line, re.IGNORECASE):
            return heading

    if 'playlist?list=' in line:
        return '## YouTube 播放列表'

    if re.match(r'^\d+[.、]\s*', line) and re.search(r'eSIM|Wise|N26|Bybit', line, re.IGNORECASE):
        return '## eSIM 与支付卡推荐'

    return None


def should_skip_heading_source_line(line):
    """Section marker lines should become headings instead of duplicated body text."""
    markers = [
        r'^短信及语音接码平台',
        r'^白嫖流量',
        r'^VPS\s*主机',
        r'^Gmail、Telegram',
        r'^👇?【?关注我不迷路',
    ]
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in markers)


def format_description_as_markdown(description):
    """Convert long YouTube descriptions into readable Markdown sections."""
    lines = [normalize_description_line(line) for line in description.splitlines()]
    lines = [line for line in lines if line]

    output = []
    current_heading = None

    for line in lines:
        heading = description_heading_for_line(line)
        if heading:
            current_heading = add_heading(output, heading, current_heading)
            if should_skip_heading_source_line(line):
                continue

        if current_heading and (
            current_heading in {
                '## 短信及语音接码平台',
                '## 白嫖流量',
                '## 关注与资源',
                '## VPS 主机推荐',
                '## 账号、礼品卡与 AI 产品充值',
                '## eSIM 与支付卡推荐',
                '## YouTube 播放列表',
            }
            or 'http' in line
        ):
            output.extend(format_resource_line(line))
            continue

        colon_items = format_colon_items(line)
        if colon_items:
            output.extend(colon_items)
            continue

        output.append(line)

    # Keep Markdown readable without creating excessive vertical gaps.
    formatted = []
    for line in output:
        if not line:
            if formatted and formatted[-1] != '':
                formatted.append('')
            continue
        if formatted and formatted[-1] and not line.startswith(('-', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '>', '#')):
            formatted.append('')
        formatted.append(line)

    return '\n'.join(formatted).strip()


def generate_article_content(video_info, video_id):
    """Generate SEO-optimized article content"""
    title = video_info['title']
    uploader = video_info.get('uploader', '')
    description = video_info.get('description', '')
    duration = video_info.get('duration', 0)

    duration_min = duration // 60 if duration else 0

    content = f"""## 视频介绍

本视频由 {uploader} 制作，时长约 {duration_min} 分钟。

"""

    # If description is long enough, format it into readable Markdown sections
    if len(description.strip()) > 200:
        content += format_description_as_markdown(description) + "\n\n"

    return content


def generate_article_content_with_body(video_info, video_id, body_md):
    """Generate article content using pre-formatted Markdown body.

    The body_md is already clean Markdown from the upstream pipeline (e.g.
    duanku blog-source.md with ads stripped). We:
      1. Add the intro header (## 视频介绍)
      2. Append body_md as-is (preserves Markdown formatting that
         format_description_as_markdown() would destroy)
      3. Append the YouTube description (formatted into Markdown sections) so
         that supplementary content the AI wrote for the YouTube description
         (适用场景, 关键步骤, 📎 资源链接, etc.) appears in the blog body too.

    Step 3 was missing in an earlier version of this function, which caused
    blog posts to lose all YouTube-description-only content. Fixed by
    appending format_description_as_markdown(description) after body_md,
    matching the behaviour of generate_article_content() (the no-body-md path).
    """
    uploader = video_info.get('uploader', '')
    description = video_info.get('description', '')
    duration = video_info.get('duration', 0)
    duration_min = duration // 60 if duration else 0

    content = f"""## 视频介绍

本视频由 {uploader} 制作，时长约 {duration_min} 分钟。

"""

    # Append the pre-formatted body as-is
    content += body_md.strip() + "\n\n"

    # Append YouTube description (formatted into Markdown) so supplementary
    # content (适用场景, 关键步骤, 📎 资源, etc.) appears in the blog body.
    if len(description.strip()) > 200:
        content += format_description_as_markdown(description) + "\n\n"

    return content


def humanize_article(content, video_title):
    """
    Apply humanizer to remove AI-generated writing patterns
    Simplified implementation based on humanizer-zh skill guidelines
    """
    lines = content.split('\n')
    humanized_lines = []
    skip_frontmatter = False
    frontmatter_end = False

    for i, line in enumerate(lines):
        # Skip front matter
        if line.strip() == '---':
            if not skip_frontmatter:
                skip_frontmatter = True
                humanized_lines.append(line)
                continue
            elif skip_frontmatter and not frontmatter_end:
                frontmatter_end = True
                humanized_lines.append(line)
                continue

        # Don't modify front matter
        if skip_frontmatter and not frontmatter_end:
            humanized_lines.append(line)
            continue

        # Skip video iframe
        if '<iframe' in line:
            humanized_lines.append(line)
            continue

        # Remove excessive emoji from headers
        if line.startswith('##'):
            # Remove multiple emojis from headings, keep at most one if relevant
            line = re.sub(r'[🎯📹📺💡🎓📝📚🔍🔗]+', '', line)
            # Remove trailing colon
            line = re.sub(r':\s*$', '', line)
            humanized_lines.append(line)
            continue

        # Format-only cleanups (safe — no content modification)
        line = re.sub(r'🚀\*\*', '', line)  # Remove rocket emoji

        # ── Word-level replacements DISABLED (v1.2) ─────────────────────────
        # These rules were designed to remove "AI writing patterns" from
        # AI-generated content. But the blog body comes from the user's
        # original Markdown article, not AI text. These substitutions:
        # 1. Destroy Chinese semantics (e.g. "很重要" → "很")
        # 2. Delete SEO keywords (e.g. "无限流量", "深入探讨" are search terms)
        # 3. Break sentence structure (e.g. removing "此外，" leaves orphaned clauses)
        # All word-level rules commented out. Format-only rules below are kept.
        # ─────────────────────────────────────────────────────────────────────
        # line = re.sub(r'真正[的]', '', line)               # ❌ breaks "真正的问题" → "的问题"
        # line = re.sub(r'终极[""]', '', line)               # ❌ deletes word without replacement
        # line = re.sub(r'"白嫖[""]', '免费', line)           # ❌ "白嫖" is a unique SEO keyword
        # line = re.sub(r'无限流量', '', line)                # ❌ deletes product keyword
        # line = re.sub(r'无限生成', '', line)                # ❌ deletes feature keyword
        # line = re.sub(r'节点无限', '', line)                # ❌ deletes product keyword
        # line = re.sub(r'4K秒开', '速度快', line)             # ❌ "4K秒开" is a differentiator, not redundant
        # line = re.sub(r'此外，', '', line)                  # ❌ removes conjunction, breaks flow
        # line = re.sub(r'深入探讨', '介绍', line)             # ❌ weakens long-tail SEO
        # line = re.sub(r'核心知识', '内容', line)             # ❌ "核心知识" more specific/unique
        # line = re.sub(r'关键信息', '信息', line)             # ❌ weakens keyword
        # line = re.sub(r'重要', '', line)                    # ❌ "很重要" → "很" — semantic destruction
        # line = re.sub(r'至关重要的', '', line)              # ❌ "至关重要的步骤" → "步骤" — info loss
        # line = re.sub(r'必不可少的', '', line)              # ❌ "必不可少的工具" → "工具" — info loss

        # ── Safe format-only rules (kept) ────────────────────────────────────
        line = re.sub(r'\*   ', '- ', line)  # Normalize list bullet spacing

        # ── Title replacement DISABLED (v1.2) ────────────────────────────────
        # Replacing the video title with "这个教程" in body text destroys SEO
        # keywords and changes meaning. The original title text should be preserved.
        # ─────────────────────────────────────────────────────────────────────
        # if video_title in line and len(video_title) > 20:
        #     short_title = video_title[:30] + '...' if len(video_title) > 30 else video_title
        #     line = line.replace(video_title, '这个教程')
        #     line = line.replace(short_title, '这个教程')

        # ── Phrase replacements DISABLED (v1.2) ──────────────────────────────
        # These also modify content; safe format-only is list bullet normalization above.
        # ─────────────────────────────────────────────────────────────────────
        # line = re.sub(r'建议在观看视频时：', '观看时：', line)
        # line = re.sub(r'无论你是……都能从中获得有价值的信息。', '', line)

        humanized_lines.append(line)

    # Clean up excessive blank lines
    result = []
    prev_blank = False
    for line in humanized_lines:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank

    return '\n'.join(result)


def save_post(content, filename, posts_dir, video_title, apply_humanizer=True):
    """Save blog post to file"""
    # Ensure directory exists
    posts_path = Path(posts_dir)
    posts_path.mkdir(parents=True, exist_ok=True)

    # Full file path
    file_path = posts_path / f"{filename}.md"

    # If file exists, add timestamp
    if file_path.exists():
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        file_path = posts_path / f"{filename}-{timestamp}.md"
        print(f"File exists, creating with timestamp: {file_path.name}")

    # Apply humanizer if enabled (default) - built-in implementation
    if apply_humanizer:
        print("🔄 Applying AI writing removal (natural language processing)...")
        content = humanize_article(content, video_title)
        print("✅ Content humanized - SEO optimized and ready")

    # Write content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Blog post created: {file_path}")
    return file_path


def deploy_to_git(blog_dir, branch='main'):
    """Deploy changes to git repository"""
    import subprocess

    if not blog_dir or not os.path.exists(blog_dir):
        print("⚠️ Blog directory not found, skipping git deployment")
        return False

    original_dir = os.getcwd()
    try:
        os.chdir(blog_dir)

        # Check if it's a git repository
        result = subprocess.run(['git', 'rev-parse', '--git-dir'],
                              capture_output=True)
        if result.returncode != 0:
            print("⚠️ Not a git repository, skipping git deployment")
            return False

        # Add changes
        print("📤 Adding changes to git...")
        subprocess.run(['git', 'add', '.'], check=True)

        # Check if there are changes to commit
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'],
                              capture_output=True)
        needs_commit = result.returncode != 0

        if needs_commit:
            # Commit changes
            print("💾 Committing changes...")
            commit_msg = f"docs: add new blog post - {datetime.now().strftime('%Y-%m-%d')}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)

            # Push to remote
            print("🚀 Pushing to remote...")
            subprocess.run(['git', 'push', 'origin', branch], check=True)
            print("✅ Successfully pushed to git repository")
        else:
            print("ℹ️ No changes to commit")

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False
    finally:
        os.chdir(original_dir)


def main():
    parser = argparse.ArgumentParser(
        description='Convert YouTube video to SEO-optimized Hexo blog post'
    )
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('-b', '--blog-dir', help='Blog directory path')
    parser.add_argument('-c', '--category', default='技术', help='Post category')
    parser.add_argument('-t', '--tags', nargs='+', default=['视频教程'], help='Post tags')
    parser.add_argument('--config', help='Path to config JSON file')
    parser.add_argument('--posts-dir', help='Override posts directory')
    parser.add_argument('--dry-run', action='store_true', help='Generate content but don\'t save')
    parser.add_argument('--no-humanizer', action='store_true', help='Skip AI writing removal (humanizer)')
    parser.add_argument('--deploy', action='store_true', help='Auto deploy to git after saving post')
    # Prefill arguments: when provided, skip YouTube fetch via yt-dlp
    parser.add_argument('--prefill-title', help='Pre-filled video title (skip YouTube fetch)')
    parser.add_argument('--prefill-description', help='Pre-filled video description (skip YouTube fetch)')
    parser.add_argument('--prefill-video-id', help='Pre-filled video ID (skip YouTube fetch)')
    parser.add_argument('--prefill-duration', type=int, default=0, help='Pre-filled duration in seconds')
    parser.add_argument('--prefill-uploader', default='', help='Pre-filled uploader name')
    parser.add_argument('--prefill-body-md', default='', help='Pre-formatted Markdown body content (bypasses format_description_as_markdown)')
    parser.add_argument('--thumbnail', help='Local custom thumbnail image path (copied to blog source/images/)')

    args = parser.parse_args()

    # Load configuration (with home directory priority)
    config = load_config(args.config, args.blog_dir)

    # Determine blog directory (priority: CLI arg > config > current dir)
    blog_dir = args.blog_dir or config.get('blog_dir', '')

    # Determine posts directory
    if args.posts_dir:
        posts_dir = args.posts_dir
    elif blog_dir:
        posts_dir = os.path.join(blog_dir, config['posts_dir'])
    else:
        posts_dir = config['posts_dir']

    # Use pre-filled data or fetch from YouTube
    if args.prefill_title and args.prefill_video_id:
        video_info = {
            'id': args.prefill_video_id,
            'title': sanitize_text_for_yaml(args.prefill_title),
            'description': args.prefill_description or '',
            'uploader': args.prefill_uploader or '',
            'upload_date': '',
            'duration': args.prefill_duration or 0,
            'thumbnail': '',
            'tags': args.tags if isinstance(args.tags, list) else [args.tags],
            'view_count': 0,
        }
        print(f"📋 Using pre-filled video info (skipped YouTube fetch)")
    else:
        video_info = get_video_info(args.url)
        if not video_info:
            print("❌ Failed to fetch video information")
            return 1

    print(f"📹 Video: {video_info['title']}")
    print(f"👤 Uploader: {video_info.get('uploader', 'N/A')}")
    if blog_dir:
        print(f"📂 Blog: {blog_dir}")

    # Generate filename
    video_id = extract_video_id(args.url) or video_info['id']
    filename = generate_english_filename(video_info['title'], video_id)
    print(f"📝 Filename: {filename}.md")

    # Handle local thumbnail: copy to blog source/images/ if provided
    if args.thumbnail and blog_dir:
        thumb_src = os.path.expanduser(args.thumbnail)
        if os.path.isfile(thumb_src):
            thumb_name = f"{filename}-cover{os.path.splitext(thumb_src)[1]}"
            images_dir = os.path.join(blog_dir, 'source', 'images')
            os.makedirs(images_dir, exist_ok=True)
            thumb_dst = os.path.join(images_dir, thumb_name)
            shutil.copy2(thumb_src, thumb_dst)
            config['local_thumbnail'] = f"/images/{thumb_name}"
            print(f"🖼️ Thumbnail copied: source/images/{thumb_name}")
        else:
            print(f"⚠️ Thumbnail not found: {thumb_src}, falling back to YouTube thumbnail")

    # Generate post content
    content = generate_post_content(video_info, config, args.category, args.tags, body_md=args.prefill_body_md or "")

    if args.dry_run:
        print("\n" + "="*60)
        print("DRY RUN - Generated content:")
        print("="*60)
        print(content[:1500] + "..." if len(content) > 1500 else content)
        print(f"\nWould save to: {os.path.join(posts_dir, filename + '.md')}")
    else:
        # Save post (with humanizer by default)
        apply_humanizer = not args.no_humanizer
        file_path = save_post(content, filename, posts_dir, video_info['title'], apply_humanizer)
        print(f"\n🎉 Post saved to: {file_path}")

        # Auto deploy if enabled
        if args.deploy or config.get('auto_deploy', False):
            print("\n🚀 Auto-deploying to git...")
            deploy_branch = config.get('deploy_branch', 'main')
            deploy_to_git(blog_dir, deploy_branch)
        else:
            print(f"\n📂 To deploy: cd {blog_dir or '.'} && hexo cl; hexo g; hexo d")

    return 0


if __name__ == '__main__':
    sys.exit(main())
