import sqlite3, sys

# 检查 test_community.db 中的用户
conn = sqlite3.connect(r'd:\projects\ai-copywriter\instance\test_community.db')
c = conn.cursor()
c.execute('SELECT id, username, email FROM users')
users = c.fetchall()
print(f'test_community.db 中共 {len(users)} 个用户:')
for u in users:
    print(f'  id={u[0]}, username={u[1]}, email={u[2]}')

# 检查 favorites
c.execute('SELECT id, user_id, post_id FROM favorites')
favs = c.fetchall()
print(f'\ntest_community.db 中共 {len(favs)} 个收藏:')
for f in favs:
    print(f'  id={f[0]}, user_id={f[1]}, post_id={f[2]}')

conn.close()

# 检查 xiaohongshu.db 中的用户
conn2 = sqlite3.connect(r'd:\projects\ai-copywriter\instance\xiaohongshu.db')
c2 = conn2.cursor()
c2.execute('SELECT id, username, email FROM users')
users2 = c2.fetchall()
print(f'\nxiaohongshu.db 中共 {len(users2)} 个用户:')
for u in users2:
    print(f'  id={u[0]}, username={u[1]}, email={u[2]}')
conn2.close()

sys.stdout.flush()
