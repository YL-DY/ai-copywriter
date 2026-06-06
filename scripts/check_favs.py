"""检查收藏页渲染"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

c = open('test_favs_output.html', encoding='utf-8').read()

data = {
    'items': [
        {
            'author': 'A',
            'content': '测试内容',
            'fav_id': 6,
            'pick_id': 'test-pick-3',
            'saved_at': '06-06 09:45',
            'title': '测试标题',
            'world_label': 'B'
        }
    ],
    'ok': True,
    'page': 1,
    'pages': 1,
    'total': 1
}

# 模拟 JS 的 map
for item in data['items']:
    preview = item['content'][:120] if item['content'] else ''
    html = '<div class="fav-card">' + \
        '<div class="fav-meta">' + (item['world_label'] or '摘录') + ' · 收藏于 ' + item['saved_at'] + '</div>' + \
        '<h3 class="fav-title">' + (item['title'] or '无标题') + '</h3>' + \
        '<p class="fav-preview">' + preview + '</p>' + \
        '<div class="fav-actions">' + \
        '<button class="btn btn-sm btn-outline" onclick="removeFav(\'' + item['pick_id'] + '\', this)">取消收藏</button>' + \
        '</div></div>'
    print('=== Generated card HTML ===')
    print(html)
    print()
    
# 再看看页面 CSS 是否正常
print('=== CSS check ===')
print('Has .fav-card:', '.fav-card' in c)
print('Has .fav-title:', '.fav-title' in c)
print('Has .fav-preview:', '.fav-preview' in c)
print('Has .fav-meta:', '.fav-meta' in c)
print('Has .fav-actions:', '.fav-actions' in c)

# favList 是否在页面中
print()
print('favList exists:', 'favList' in c)
print('favEmpty exists (hidden):', 'favEmpty' in c)
