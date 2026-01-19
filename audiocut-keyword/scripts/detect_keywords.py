#!/usr/bin/env python3
"""
关键字识别脚本 - 在转录文本中查找关键字并定位时间戳
"""

import json
import sys
import re
from pathlib import Path

def load_keywords(config_file):
    """加载关键字配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config.get('keywords', [])

def find_keyword_positions(transcript_data, keywords):
    """
    在转录文本中查找关键字位置

    Args:
        transcript_data: 转录数据（包含 chars 数组）
        keywords: 关键字列表

    Returns:
        匹配结果列表，每项包含 keyword, start, end, context
    """
    full_text = transcript_data['full_text']
    chars = transcript_data['chars']
    matches = []

    print(f"🔍 开始搜索关键字...")
    print(f"   文本长度: {len(full_text)} 字符")
    print(f"   关键字数量: {len(keywords)}")

    for keyword in keywords:
        # 在文本中查找所有匹配位置
        pattern = re.escape(keyword)
        for match in re.finditer(pattern, full_text):
            start_idx = match.start()
            end_idx = match.end()

            # 获取时间戳
            if start_idx < len(chars) and end_idx <= len(chars):
                start_time = chars[start_idx]['start']
                end_time = chars[end_idx - 1]['end']

                # 获取上下文（前后各10个字符）
                context_start = max(0, start_idx - 10)
                context_end = min(len(full_text), end_idx + 10)
                context = full_text[context_start:context_end]

                matches.append({
                    'keyword': keyword,
                    'start': start_time,
                    'end': end_time,
                    'position': start_idx,
                    'context': context,
                    'matched_text': full_text[start_idx:end_idx]
                })

                print(f"   ✓ 找到 '{keyword}' 在 {start_time:.2f}s-{end_time:.2f}s")

    print(f"✅ 搜索完成，共找到 {len(matches)} 处匹配")
    return matches

def generate_delete_plan(matches, buffer_before=0.5, buffer_after=0.5):
    """
    生成删除计划（合并重叠的时间段）

    Args:
        matches: 匹配结果列表
        buffer_before: 前置缓冲时间（秒）
        buffer_after: 后置缓冲时间（秒）

    Returns:
        删除片段列表 [(start, end), ...]
    """
    if not matches:
        return []

    # 添加缓冲时间
    segments = []
    for m in matches:
        start = max(0, m['start'] - buffer_before)
        end = m['end'] + buffer_after
        segments.append((start, end))

    # 按开始时间排序
    segments.sort()

    # 合并重叠的片段
    merged = [segments[0]]
    for current in segments[1:]:
        last = merged[-1]
        if current[0] <= last[1]:  # 有重叠
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)

    return merged
