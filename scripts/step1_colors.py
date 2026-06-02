import re

with open('templates/base.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. 替换 Google Fonts 导入
c = c.replace(
    "@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&family=Caveat:wght@700&display=swap');",
    "@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Noto+Serif+SC:wght@400;600;700&display=swap');"
)

# 2. 替换 CSS 变量
old_vars = """:root {
            --bg-gradient: linear-gradient(160deg, #0b0f1a 0%, #14172a 40%, #0f172a 70%, #0a0f1f 100%);
            --bg-soft: rgba(11, 15, 26, 0.7);
            --bg-card: rgba(20, 23, 42, 0.45);
            --bg-hover: rgba(11, 15, 26, 0.35);
            --text-primary: #e2e8f0;
            --text-secondary: #f1f5f9;
            --text-muted: #64748b;
            --text-subtle: #475569;
            --border-color: rgba(51, 65, 85, 0.2);
            --border-hover: rgba(51, 65, 85, 0.35);
            --input-bg: rgba(11, 15, 26, 0.5);
            --toast-bg: rgba(20, 23, 42, 0.95);
            --bg-ornament: radial-gradient(ellipse at 15% 50%, rgba(56, 189, 248, 0.04) 0%, transparent 50%),
                           radial-gradient(ellipse at 85% 30%, rgba(167, 139, 250, 0.03) 0%, transparent 50%);
            --card-shadow: 0 4px 32px rgba(0,0,0,0.2);
        }"""

new_vars = """:root {
            --bg-primary: #121212;
            --bg-secondary: #18181B;
            --bg-soft: rgba(18, 18, 18, 0.85);
            --bg-card: rgba(255, 255, 255, 0.04);
            --bg-hover: rgba(255, 255, 255, 0.06);
            --brand-primary: #D4A373;
            --brand-secondary: #E9C46A;
            --text-primary: #F5F5F5;
            --text-secondary: #A1A1AA;
            --text-muted: #A1A1AA;
            --text-subtle: #71717A;
            --border-color: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.12);
            --input-bg: rgba(255, 255, 255, 0.04);
            --toast-bg: rgba(24, 24, 27, 0.95);
            --bg-ornament: radial-gradient(ellipse at 20% 50%, rgba(212, 163, 115, 0.04) 0%, transparent 50%),
                           radial-gradient(ellipse at 80% 30%, rgba(233, 196, 106, 0.03) 0%, transparent 50%);
            --card-shadow: 0 4px 40px rgba(0,0,0,0.4);
            --bg-gradient: linear-gradient(160deg, #121212 0%, #18181B 40%, #121212 70%, #18181B 100%);
        }"""

c = c.replace(old_vars, new_vars)

# 3. 替换 body.light
old_light = """        body.light {
            --bg-gradient: linear-gradient(160deg, #f8fafc 0%, #e2e8f0 40%, #f1f5f9 70%, #f0f4f8 100%);
            --bg-soft: rgba(255, 255, 255, 0.85);
            --bg-card: rgba(255, 255, 255, 0.65);
            --bg-hover: rgba(255, 255, 255, 0.45);
            --text-primary: #1e293b;
            --text-secondary: #0f172a;
            --text-muted: #64748b;
            --text-subtle: #94a3b8;
            --border-color: rgba(148, 163, 184, 0.2);
            --border-hover: rgba(148, 163, 184, 0.35);
            --input-bg: rgba(255, 255, 255, 0.6);
            --toast-bg: rgba(255, 255, 255, 0.95);
            --bg-ornament: radial-gradient(ellipse at 15% 50%, rgba(56, 189, 248, 0.06) 0%, transparent 50%),
                           radial-gradient(ellipse at 85% 30%, rgba(167, 139, 250, 0.05) 0%, transparent 50%);
            --card-shadow: 0 4px 32px rgba(0,0,0,0.06);
        }"""

new_light = """        body.light {
            --bg-primary: #FAFAF9;
            --bg-secondary: #F5F5F0;
            --bg-soft: rgba(250, 250, 249, 0.9);
            --bg-card: rgba(255, 255, 255, 0.7);
            --bg-hover: rgba(0, 0, 0, 0.03);
            --brand-primary: #D4A373;
            --brand-secondary: #E9C46A;
            --text-primary: #1C1917;
            --text-secondary: #44403C;
            --text-muted: #78716C;
            --text-subtle: #A8A29E;
            --border-color: rgba(0, 0, 0, 0.08);
            --border-hover: rgba(0, 0, 0, 0.12);
            --input-bg: rgba(0, 0, 0, 0.03);
            --toast-bg: rgba(255, 255, 255, 0.95);
            --bg-ornament: radial-gradient(ellipse at 20% 50%, rgba(212, 163, 115, 0.06) 0%, transparent 50%),
                           radial-gradient(ellipse at 80% 30%, rgba(233, 196, 106, 0.04) 0%, transparent 50%);
            --card-shadow: 0 4px 32px rgba(0,0,0,0.06);
            --bg-gradient: linear-gradient(160deg, #FAFAF9 0%, #F5F5F0 40%, #FAFAF9 70%, #F5F5F0 100%);
        }"""

c = c.replace(old_light, new_light)

# 4. 替换 body 字体
c = c.replace(
    'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;',
    'font-family: "Noto Serif SC", "Cormorant Garamond", Georgia, "Times New Roman", serif;'
)

# 5. Logo 改暖金 + Cormorant Garamond
c = c.replace(
    'font-family: "Dancing Script", "Caveat", cursive;',
    'font-family: "Cormorant Garamond", "Playfair Display", serif;'
)
c = c.replace(
    '''background: linear-gradient(135deg, #38bdf8 0%, #a78bfa 50%, #f472b6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: "Dancing Script", "Caveat", cursive;''',
    '''background: linear-gradient(90deg, #D4A373, #E9C46A);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: "Cormorant Garamond", "Playfair Display", serif;'''
)

# 6. Splash 品牌色也改
c = c.replace(
    '''background: linear-gradient(135deg, #38bdf8 0%, #a78bfa 40%, #f472b6 70%, #38bdf8 100%);''',
    '''background: linear-gradient(90deg, #D4A373, #E9C46A, #D4A373);'''
)

# 7. 替换所有 blue 主题的 hover/focus 颜色为金色
c = c.replace('border-color: rgba(56, 189, 248, 0.25);', 'border-color: rgba(212, 163, 115, 0.25);')
c = c.replace('rgba(56,189,248,0.06)', 'rgba(212,163,115,0.06)')
c = c.replace('rgba(56, 189, 248, 0.04)', 'rgba(212, 163, 115, 0.04)')
c = c.replace('rgba(56, 189, 248, 0.08)', 'rgba(212, 163, 115, 0.08)')
c = c.replace('rgba(56,189,248,0.08)', 'rgba(212,163,115,0.08)')
c = c.replace('rgba(56, 189, 248, 0.15)', 'rgba(212, 163, 115, 0.15)')
c = c.replace('rgba(56, 189, 248, 0.25)', 'rgba(212, 163, 115, 0.25)')
c = c.replace('rgba(37, 99, 235, 0.25)', 'rgba(212, 163, 115, 0.3)')
c = c.replace('rgba(37, 99, 235, 0.35)', 'rgba(212, 163, 115, 0.4)')

# theme-toggle hover 颜色
c = c.replace('border-color: #38bdf8;\n            color: #38bdf8;', 'border-color: #D4A373;\n            color: #D4A373;')

# 活跃导航颜色
c = c.replace("color: #38bdf8;", "color: #D4A373;")
c = c.replace("color: #60a5fa;", "color: #D4A373;")

# 分页 hover
c = c.replace('color: #38bdf8; }', 'color: #D4A373; }')

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Step 1 done: 全局配色 + Logo + 字体 + Splash 品牌色")
