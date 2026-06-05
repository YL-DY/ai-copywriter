import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
import importlib
for w in ['youth','unrequited','nostalgia','lonely','warmth','romance','wildfire','mountains']:
    m = importlib.import_module('literary.worlds.' + w)
    print(f"{w}: {len(m.SAMPLES)} samples")
