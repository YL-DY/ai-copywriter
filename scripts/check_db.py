import sqlite3, os, sys
from datetime import datetime

dbs = [
    r'd:\projects\ai-copywriter\instance\xiaohongshu.db',
    r'd:\projects\instance\xiaohongshu.db',
    r'd:\projects\ai-copywriter\instance\test_community.db',
]

for db_path in dbs:
    if not os.path.exists(db_path):
        print(f'{db_path} 不存在')
        continue
    size = os.path.getsize(db_path)
    mtime = os.path.getmtime(db_path)
    print(f'=== {db_path} ===')
    print(f'  大小: {size} bytes, 修改时间: {datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")}')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in c.fetchall()]
    print(f'  表: {tables}')
    for t in tables:
        try:
            c.execute(f'SELECT COUNT(*) FROM "{t}"')
            cnt = c.fetchone()[0]
            print(f'    {t}: {cnt} 条记录')
        except Exception as e:
            print(f'    {t}: ERROR - {e}')
    conn.close()
    print()

sys.stdout.flush()
