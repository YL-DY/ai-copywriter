"""检查摘录内容是否有HTML问题"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ['DATABASE_URL'] = 'sqlite:///test_community.db'
os.environ['DEEPSEEK_API_KEY'] = 'sk-test'

from literary import get_daily_pick

picks = get_daily_pick(user_id=0, max_count=1)
if picks:
    pick = picks[0]
    idx = 0
    html_out = f'''<div class="carousel-slide" data-index="{idx}">
            <div class="slide-world">{pick['world_label']}</div>
            <div class="slide-title">{pick['title']}</div>
            <div class="slide-content">{pick['content']}</div>
            <div class="slide-author">{pick['author']}</div>
        </div>'''
    print('=== Simulated render ===')
    print(html_out[:600])
    
    print('\n=== Content check ===')
    content = pick['content']
    print('Has <script>:', '<script' in content.lower())
    print('Has </', '</' in content)
    print('Has backtick:', '`' in content)
    print('Has ${:', '${' in content)
    # 检查是否有 Jinja2 语法
    print('Has {%:', '{%' in content)
    print('Has {{:', '{{' in content)
    print('Has }}:', '}}' in content)
    print('Content first 100:', repr(content[:100]))
else:
    print('No picks')
