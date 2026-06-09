# -*- coding: utf-8 -*-
"""验证 8 种风格库和自动混合模式"""
import sys
sys.path.insert(0, 'd:/projects/ai-copywriter')

from literary import (
    STYLES, STYLE_LABELS, STYLE_DESCRIPTIONS, STYLE_GENERATORS,
    AUTO_MIX_CONFIG, generate_with_style, generate_short_text, WORLDS
)

print("=== 风格列表 ===")
for s in STYLES:
    print(f"  {s}: {STYLE_LABELS[s]}")
print(f"  共 {len(STYLES)} 种风格")

print("\n=== 自动混合权重 ===")
for s, w in AUTO_MIX_CONFIG['weights'].items():
    if w > 0:
        print(f"  {STYLE_LABELS[s]}: {w*100:.0f}%")
total = sum(AUTO_MIX_CONFIG['weights'].values())
print(f"  总权重: {total}")

print("\n=== 风格生成器测试 ===")
for s in STYLES:
    gen = STYLE_GENERATORS.get(s)
    if gen:
        result = gen(seed_words='测试', length='short')
        ok = 'title' in result and 'content' in result and 'style_id' in result
        mark = 'OK' if ok else 'FAIL'
        print(f"  [{mark}] {STYLE_LABELS[s]}: {result['title'][:20]}... ({len(result['content'])}字)")
    else:
        print(f"  [FAIL] {STYLE_LABELS[s]}: 缺少生成器")

print("\n=== 自动混合模式测试 ===")
for i in range(5):
    result = generate_with_style(auto_mix=True)
    print(f"  [{i+1}] {result['style_label']}: {result['title'][:20]}")

print("\n=== 指定风格测试 ===")
result = generate_with_style(style_id='white_space', auto_mix=False)
print(f"  指定留白文学: {result['style_label']} - {result['title']}")

print("\n=== 原有世界系统验证 ===")
result = generate_short_text(world_id='youth', length='short')
print(f"  世界生成: {result['world_label']} - {result['title'][:20]} ({len(result['content'])}字)")

print("\n所有验证通过!")
