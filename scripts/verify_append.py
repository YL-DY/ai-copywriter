import sys, os, importlib
sys.stdout.reconfigure(encoding='utf-8')
# 清除缓存
for root, dirs, files in os.walk('.'):
    for d in dirs:
        if d == '__pycache__':
            import shutil
            try:
                shutil.rmtree(os.path.join(root, d))
            except:
                pass

sys.path.insert(0, '.')
for w in ['youth','unrequited','nostalgia','lonely','warmth','romance','wildfire','mountains']:
    m = importlib.import_module(f'literary.worlds.{w}')
    print(f'{w}: {len(m.SAMPLES)} samples')
