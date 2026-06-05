import sys, re
sys.stdout.reconfigure(encoding='utf-8')
c = open('app.py', 'r', encoding='utf-8').read()
print(f"Total lines: {len(c.splitlines())}")
routes = re.findall(r"@app\.route\(['\"]([^'\"]+)['\"]", c)
print(f"Routes: {len(routes)}")
for r in routes:
    print(f"  {r}")
