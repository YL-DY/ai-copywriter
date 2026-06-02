with open('templates/base.html', 'r', encoding='utf-8') as f:
    c = f.read()

# splash-star 颜色
c = c.replace(
    '''.splash-star {
            position: absolute;
            width: 2px; height: 2px;
            background: #38bdf8;
            border-radius: 50%;
            opacity: 0;
            animation: starTwinkle 2s ease-in-out infinite;
        }''',
    '''.splash-star {
            position: absolute;
            width: 2px; height: 2px;
            background: #D4A373;
            border-radius: 50%;
            opacity: 0;
            animation: starTwinkle 2s ease-in-out infinite;
        }'''
)

# splash glow
c = c.replace('rgba(56,189,248,0.08)', 'rgba(212,163,115,0.08)')

# navbar brand text-shadow
c = c.replace('text-shadow: 0 0 30px rgba(56, 189, 248, 0.15);', 'text-shadow: 0 0 30px rgba(212, 163, 115, 0.15);')
c = c.replace('text-shadow: 0 0 50px rgba(56, 189, 248, 0.25);', 'text-shadow: 0 0 50px rgba(212, 163, 115, 0.25);')

# splash-line
c = c.replace('rgba(56,189,248,0.3), rgba(167,139,250,0.3)', 'rgba(212,163,115,0.3), rgba(233,196,106,0.3)')

# particles canvas
c = c.replace(
    "ctx.fillStyle = 'rgba(56, 189, 248, ' + this.opacity + ')';",
    "ctx.fillStyle = 'rgba(212, 163, 115, ' + this.opacity + ')';"
)
c = c.replace(
    "ctx.strokeStyle = 'rgba(56, 189, 248, ' + (0.05 * (1 - dist / 120)) + ')';",
    "ctx.strokeStyle = 'rgba(212, 163, 115, ' + (0.05 * (1 - dist / 120)) + ')';"
)

# 剩余的 #38bdf8 在 JS 中（theme-toggle 的 JS 代码）
c = c.replace("'\\u2600\\ufe0f' : '\\ud83c\\udf19'", "'☀️' : '🌙'")

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Clean done")
