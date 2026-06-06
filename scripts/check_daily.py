"""检查每日页面渲染"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ['DATABASE_URL'] = 'sqlite:///test_community.db'
os.environ['DEEPSEEK_API_KEY'] = 'sk-test'
from app import app
import re

client = app.test_client()
client.post('/auth/register', data={'username':'testdaily','email':'td@t.com','password':'123456'})
client.post('/auth/login', data={'username':'testdaily','password':'123456'})

r = client.get('/daily')
html = r.text

# 检查关键元素
print("=== 页面检查 ===")
print("Has daily-page:", 'daily-page' in html)
print("Has carousel-track:", 'carousel-track' in html)
print("Has slide-content:", 'slide-content' in html)
print("Has slide-title:", 'slide-title' in html)

# 检查JS是否有语法问题 - 提取<script>区
script_start = html.find('<script>') + 8
script_end = html.find('</script>', script_start)
if script_start > 8 and script_end > script_start:
    js = html[script_start:script_end]
    # 检查模板字符串是否有冲突
    has_backtick = '`' in js
    print("Has backtick template strings:", has_backtick)
    
    # 检查pick.content中是否有反引号导致断链
    # 找一个示例摘录，看内容渲染
    for pick in ['那个跑在最前面的人', '夏天的蒲扇', '妈妈的饺子']:
        if pick in html:
            print(f"Content '{pick}' found in HTML")
    
    print("JS length:", len(js))
    print("First 100 chars of JS:", js[:100])
else:
    print("No script block found!")
    print("Script start:", script_start)
    print("Script end:", script_end)
