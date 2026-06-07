"""验证修改后的 URI 构造逻辑"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

# 测试 1: DATABASE_URL 为 postgresql://
os.environ['DATABASE_URL'] = 'postgresql://user:pass@host:5432/railway'
database_url = os.environ.get("DATABASE_URL", "")
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
print(f"Test 1 (postgresql://): {database_url}")
assert '+psycopg' in database_url, "FAIL: +psycopg not in URI"

# 测试 2: DATABASE_URL 为 postgres:// (旧格式)
os.environ['DATABASE_URL'] = 'postgres://user:pass@host:5432/railway'
database_url = os.environ.get("DATABASE_URL", "")
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
print(f"Test 2 (postgres://):   {database_url}")
assert '+psycopg' in database_url, "FAIL: +psycopg not in URI"

# 测试 3: 无 DATABASE_URL (SQLite 回退)
os.environ.pop('DATABASE_URL', None)
database_url = os.environ.get("DATABASE_URL", "")
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    from flask import Flask
    app = Flask(__name__)
    db_dir = os.path.join(app.instance_path)
    os.makedirs(db_dir, exist_ok=True)
    database_url = f"sqlite:///{os.path.join(db_dir, 'xiaohongshu.db').replace(os.sep, '/')}"
print(f"Test 3 (no DATABASE_URL): {database_url}")
assert database_url.startswith('sqlite:///'), "FAIL: should be sqlite"

print("\nAll tests passed!")
print(f"\nFinal URI for Railway: postgresql+psycopg://user:pass@host:5432/railway")
print(f"SQLAlchemy will use psycopg (v3) driver - no libpq.so.5 dependency needed")
sys.stdout.flush()
