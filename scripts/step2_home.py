with open('templates/home.html', 'r', encoding='utf-8') as f:
    c = f.read()

# ==================== 1. Hero 区重构 ====================
# 替换标题
c = c.replace(
    '''<span class="hero-brand-word">InkFlow</span>
            <span class="hero-title-line">AI 驱动的新一代</span>
            <span class="hero-title-line">营销文案创作平台</span>''',
    '''<span class="hero-brand-word">InkFlow</span>
            <span class="hero-title-line">每个人都有故事</span>
            <span class="hero-title-line">只是缺一句恰好表达的话</span>'''
)

# 替换副标题
c = c.replace(
    '''几秒钟生成高质量广告文案、品牌内容与社交媒体营销文案''',
    '''让文字替你说出那些<br>难以开口的情绪与故事'''
)

# 替换 CTA 按钮文字和样式
c = c.replace(
    '''<a href="#" class="hero-cta" id="ctaBtn">
            立即体验 →
        </a>''',
    '''<a href="#" class="hero-cta" id="ctaBtn">
            开始书写 →
        </a>'''
)

# 替换 CTA 按钮样式
c = c.replace(
    '''background: linear-gradient(135deg, #1d4ed8, #2563eb);
    color: white;
    text-decoration: none;
    box-shadow: 0 4px 24px rgba(37, 99, 235, 0.3);''',
    '''background: #D4A373;
    color: #121212;
    text-decoration: none;
    box-shadow: 0 4px 24px rgba(212, 163, 115, 0.3);'''
)
c = c.replace(
    '''box-shadow: 0 8px 32px rgba(37, 99, 235, 0.4);''',
    '''box-shadow: 0 8px 32px rgba(212, 163, 115, 0.4);'''
)

# 替换特性标签
c = c.replace(
    '''<div class="hero-feature">✨ 7 种文案风格</div>
            <div class="hero-feature">⚡ 秒级生成</div>
            <div class="hero-feature">🎯 精准营销</div>''',
    '''<div class="hero-feature">📖 治愈系文字</div>
            <div class="hero-feature">💫 情绪表达</div>
            <div class="hero-feature">🌙 深夜故事</div>'''
)

# 替换 brand-word 颜色
c = c.replace(
    '''background: linear-gradient(135deg, #38bdf8 0%, #a78bfa 40%, #f472b6 70%, #38bdf8 100%);''',
    '''background: linear-gradient(90deg, #D4A373, #E9C46A, #D4A373);'''
)

# 替换 font-family
c = c.replace(
    'font-family: "Dancing Script", "Caveat", cursive;',
    'font-family: "Cormorant Garamond", "Playfair Display", serif;'
)

# ==================== 2. 情绪展示区（Hero 下方新增） ====================
# 在 heroPage 后面添加情绪卡片模块
hero_end = '</div>\n</div>\n\n<div id="generatePage">'
emotion_section = '''</div>
</div>

<!-- ===== 情绪展示区 ===== -->
<div class="emotion-section" id="emotionSection">
    <h2 class="emotion-title">有些话 总能在深夜击中人心</h2>
    <div class="emotion-cards">
        <div class="emotion-card">
            <div class="emotion-card-icon">🌙</div>
            <div class="emotion-card-text">"后来我才明白，<br>遗憾不是没得到，<br>而是差一点就得到了。"</div>
            <div class="emotion-card-divider"></div>
            <div class="emotion-card-author">—— 深夜书店</div>
        </div>
        <div class="emotion-card">
            <div class="emotion-card-icon">✨</div>
            <div class="emotion-card-text">"你以为时间会冲淡一切，<br>可它只是教会你习惯。"</div>
            <div class="emotion-card-divider"></div>
            <div class="emotion-card-author">—— 深夜书店</div>
        </div>
        <div class="emotion-card">
            <div class="emotion-card-icon">📖</div>
            <div class="emotion-card-text">"故事的结局并不重要，<br>重要的是你曾认真爱过。"</div>
            <div class="emotion-card-divider"></div>
            <div class="emotion-card-author">—— 深夜书店</div>
        </div>
    </div>
</div>

<div id="generatePage">'''

c = c.replace(hero_end, emotion_section)

# ==================== 3. 生成页面优化 ====================
# 标题和副标题
c = c.replace(
    '''<h1>生成文案<small>告诉我你的产品，剩下的交给 InkFlow</small></h1>''',
    '''<h1>告诉我你的故事<small>剩下的 交给 InkFlow</small></h1>'''
)

# label 和 textarea placeholder
c = c.replace(
    '''<label>你想推广什么产品？</label>
            <textarea name="product" rows="2" placeholder="例如：一杯手冲咖啡、一款小众香水、一本自我提升的书..." required style="font-family:inherit;">''',
    '''<label>此刻你想表达什么？</label>
            <textarea name="product" rows="4" placeholder="例如：&#10;我喜欢了一个人很多年，&#10;却始终没能说出口..." required style="font-family:inherit;min-height:160px;">'''
)

# 详情 placeholder 换更温暖版本
c = c.replace(
    '''textarea name="custom_prompt" rows="3" placeholder="例如：面向大学生 / 突出性价比 / 语气活泼可爱 / 强调环保理念..."''',
    '''textarea name="custom_prompt" rows="3" placeholder="例如：写给那个放不下的人 / 想要温暖治愈的语气 / 像老朋友在深夜谈心..."'''
)

# 生成按钮
c = c.replace(
    '''<button type="submit" class="btn btn-primary" id="generateBtn" style="width:100%;font-size:15px;padding:14px;">
                ✨ 让灵笔为你创作
            </button>''',
    '''<button type="submit" class="btn btn-primary" id="generateBtn" style="width:100%;font-size:15px;padding:16px;border-radius:14px;">
                ✨ 让文字替我说话
            </button>'''
)

# ==================== 4. 结果页重构 ====================
# 结果卡片整体改为情绪卡片样式
c = c.replace(
    '''<div class="result-card">
            <div class="result-card-cover">
                <div class="result-card-ornament"></div>
                <div class="result-card-header">
                    <div class="result-card-meta">
                        <span class="result-style-tag">{{ style_icons.get(reuse_style, '📝') }} {{ reuse_style or '' }}</span>
                        <span class="result-tokens">⚡ {{ result_tokens }} tokens</span>
                    </div>
                    <div class="result-actions">
                        {% if last_history_id and last_history_id > 0 %}
                        <form method="POST" action="{{ url_for('toggle_favorite', history_id=last_history_id) }}" style="display:inline;" class="fav-form">
                            <button type="submit" class="btn-sm btn-outline" title="收藏">☆</button>
                        </form>
                        {% endif %}
                        <button onclick="exportText('txt')" class="btn-sm btn-outline">📄 TXT</button>
                        <button onclick="exportText('md')" class="btn-sm btn-outline">📝 MD</button>
                        <button onclick="copyText()" class="btn-sm btn-success">📋 复制</button>
                    </div>
                </div>
                {% if result_title %}
                <div class="result-card-headline">
                    <div class="result-card-headline-accent"></div>
                    <div class="result-card-title">{{ result_emoji }} {{ result_title }}</div>
                </div>
                {% endif %}
            </div>
            {% if result_tags %}
            <div class="result-card-tags-section">
                {% for tag in result_tags %}
                <span class="result-tag">#{{ tag }}</span>
                {% endfor %}
            </div>
            {% endif %}
            <div class="result-card-body">
                <div class="result-box" id="resultBox">{{ result_content }}</div>
            </div>
            <div class="result-card-rewrite">
                <div class="rewrite-label">✏️ 二次编辑</div>
                <div class="rewrite-buttons">
                    <button class="btn-sm btn-rewrite" data-action="shorter">📏 改短一点</button>
                    <button class="btn-sm btn-rewrite" data-action="premium">👑 更高级</button>
                    <button class="btn-sm btn-rewrite" data-action="xiaohongshu">📱 更适合小红书</button>
                    <button class="btn-sm btn-rewrite" data-action="emotional">💫 更有情绪感</button>
                    <button class="btn-sm btn-rewrite" data-action="story">📖 故事化</button>
                </div>
                <div style="margin-top:10px;">
                    <button class="btn-sm btn-outline" id="analyzeBtn" style="font-size:12px;">🔍 AI 分析建议</button>
                </div>
                <div id="analyzeResult" style="display:none;margin-top:14px;padding:16px;background:rgba(11,15,26,0.4);border-radius:12px;border:1px solid rgba(51,65,85,0.15);">
                    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;" id="scoreBars"></div>
                    <div style="margin-bottom:12px;"><span style="font-size:12px;color:#38bdf8;font-weight:600;">✅ 优点</span><div id="strengthsList" style="font-size:13px;color:#94a3b8;margin-top:4px;"></div></div>
                    <div style="margin-bottom:12px;"><span style="font-size:12px;color:#f87171;font-weight:600;">⚠️ 可改进</span><div id="weaknessesList" style="font-size:13px;color:#94a3b8;margin-top:4px;"></div></div>
                    <div><span style="font-size:12px;color:#a78bfa;font-weight:600;">💡 优化建议</span><div id="tipsList" style="font-size:13px;color:#94a3b8;margin-top:4px;"></div></div>
                </div>
            </div>
        </div>''',
    '''<div class="result-card">
            <div class="result-card-header">
                <div class="result-card-badge">✦ InkFlow 为你写下：</div>
            </div>
            {% if result_title %}
            <div class="result-card-title-wrap">
                <div class="result-card-title">{{ result_emoji }} {{ result_title }}</div>
            </div>
            {% endif %}
            <div class="result-card-body">
                <div class="result-box" id="resultBox">{{ result_content }}</div>
            </div>
            {% if result_tags %}
            <div class="result-card-tags-section">
                {% for tag in result_tags %}
                <span class="result-tag">#{{ tag }}</span>
                {% endfor %}
            </div>
            {% endif %}
            <div class="result-card-footer">
                <button onclick="copyText()" class="btn-result-action">📋 复制</button>
                {% if last_history_id and last_history_id > 0 %}
                <form method="POST" action="{{ url_for('toggle_favorite', history_id=last_history_id) }}" style="display:inline;" class="fav-form">
                    <button type="submit" class="btn-result-action" title="收藏">☆ 收藏</button>
                </form>
                {% endif %}
                <button onclick="shareCard()" class="btn-result-action">📤 分享</button>
            </div>
            <div class="result-card-rewrite">
                <div class="rewrite-label">✏️ 二次编辑</div>
                <div class="rewrite-buttons">
                    <button class="btn-sm btn-rewrite" data-action="shorter">📏 改短一点</button>
                    <button class="btn-sm btn-rewrite" data-action="premium">👑 更高级</button>
                    <button class="btn-sm btn-rewrite" data-action="xiaohongshu">📱 更适合小红书</button>
                    <button class="btn-sm btn-rewrite" data-action="emotional">💫 更有情绪感</button>
                    <button class="btn-sm btn-rewrite" data-action="story">📖 故事化</button>
                </div>
                <div style="margin-top:10px;">
                    <button class="btn-sm btn-outline" id="analyzeBtn" style="font-size:12px;">🔍 AI 分析建议</button>
                </div>
                <div id="analyzeResult" style="display:none;margin-top:14px;padding:16px;background:rgba(255,255,255,0.03);border-radius:12px;border:1px solid rgba(255,255,255,0.06);">
                    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;" id="scoreBars"></div>
                    <div style="margin-bottom:12px;"><span style="font-size:12px;color:#D4A373;font-weight:600;">✅ 优点</span><div id="strengthsList" style="font-size:13px;color:#A1A1AA;margin-top:4px;"></div></div>
                    <div style="margin-bottom:12px;"><span style="font-size:12px;color:#f87171;font-weight:600;">⚠️ 可改进</span><div id="weaknessesList" style="font-size:13px;color:#A1A1AA;margin-top:4px;"></div></div>
                    <div><span style="font-size:12px;color:#E9C46A;font-weight:600;">💡 优化建议</span><div id="tipsList" style="font-size:13px;color:#A1A1AA;margin-top:4px;"></div></div>
                </div>
            </div>
        </div>'''
)

# 替换 loading 文字
c = c.replace(
    '''<div class="loading-text">灵笔正在创作中</div>''',
    '''<div class="loading-text">正在为你书写</div>'''
)
c = c.replace(
    '''<div class="loading-hint">为你精心打磨每一段文案...</div>''',
    '''<div class="loading-hint">每一字每一句 都是为你准备的...</div>'''
)

# ==================== 5. 替换颜色引用 ====================
# 替换所有蓝色引用为暖金色
c = c.replace('rgba(56,189,248,0.06)', 'rgba(212,163,115,0.06)')
c = c.replace('rgba(56, 189, 248, 0.06)', 'rgba(212, 163, 115, 0.06)')
c = c.replace('rgba(56, 189, 248, 0.08)', 'rgba(212, 163, 115, 0.08)')
c = c.replace('rgba(56,189,248,0.08)', 'rgba(212,163,115,0.08)')
c = c.replace('rgba(56, 189, 248, 0.25)', 'rgba(212, 163, 115, 0.25)')
c = c.replace('#38bdf8', '#D4A373')
c = c.replace('#a78bfa', '#E9C46A')

# 替换结果卡片的浅色背景
c = c.replace('rgba(11, 15, 26, 0.6)', 'rgba(255, 255, 255, 0.05)')
c = c.replace('rgba(51, 65, 85, 0.2)', 'rgba(255, 255, 255, 0.08)')
c = c.replace('rgba(51, 65, 85, 0.25)', 'rgba(255, 255, 255, 0.08)')

# 粒子数量减少 50%（80 -> 40）
c = c.replace('for (var i = 0; i < 80; i++) particles.push(new Particle());', 'for (var i = 0; i < 40; i++) particles.push(new Particle());')

# 移除粒子之间的连线（科技线条）
c = c.replace(
    '''    for (var i = 0; i < particles.length; i++) {
        for (var j = i + 1; j < particles.length; j++) {
            var dx = particles[i].x - particles[j].x;
            var dy = particles[i].y - particles[j].y;
            var dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 120) {
                ctx.beginPath();
                ctx.moveTo(particles[i].x, particles[i].y);
                ctx.lineTo(particles[j].x, particles[j].y);
                ctx.strokeStyle = 'rgba(212, 163, 115, ' + (0.05 * (1 - dist / 120)) + ')';
                ctx.lineWidth = 0.5;
                ctx.stroke();
            }
        }
    }''',
    ''
)

# ==================== 6. 新增 CSS 样式 ====================
# 在 </style> 前插入新样式
new_css = '''
/* ===== 深夜书店 情绪卡片区 ===== */
.emotion-section {
    max-width: 800px;
    margin: 80px auto 60px;
    padding: 0 20px;
    text-align: center;
}
.emotion-title {
    font-family: "Cormorant Garamond", "Noto Serif SC", serif;
    font-size: 28px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 40px;
    letter-spacing: 2px;
}
.emotion-cards {
    display: flex;
    gap: 24px;
    justify-content: center;
    flex-wrap: wrap;
}
.emotion-card {
    flex: 1;
    min-width: 220px;
    max-width: 320px;
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 20px;
    padding: 32px 24px;
    text-align: center;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: default;
}
.emotion-card:hover {
    transform: translateY(-6px);
    background: rgba(255, 255, 255, 0.07);
    border-color: rgba(212, 163, 115, 0.15);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
}
.emotion-card-icon {
    font-size: 32px;
    margin-bottom: 16px;
}
.emotion-card-text {
    font-size: 15px;
    line-height: 1.8;
    color: var(--text-primary);
    font-weight: 400;
    letter-spacing: 0.5px;
}
.emotion-card-divider {
    width: 40px;
    height: 2px;
    background: linear-gradient(90deg, #D4A373, #E9C46A);
    margin: 16px auto 12px;
    border-radius: 2px;
}
.emotion-card-author {
    font-size: 12px;
    color: var(--text-subtle);
    letter-spacing: 1px;
}
@media (max-width: 600px) {
    .emotion-section { margin: 40px auto; }
    .emotion-title { font-size: 22px; }
    .emotion-card { min-width: 100%; max-width: 100%; padding: 24px 20px; }
}

/* ===== 情绪卡片结果页 ===== */
.result-card {
    border-radius: 24px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3);
    animation: cardUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
    padding: 32px;
}
.result-card-header {
    margin-bottom: 24px;
}
.result-card-badge {
    display: inline-block;
    font-size: 13px;
    color: #D4A373;
    letter-spacing: 2px;
    font-weight: 500;
    font-family: "Cormorant Garamond", "Noto Serif SC", serif;
    border-bottom: 1px solid rgba(212, 163, 115, 0.2);
    padding-bottom: 8px;
}
.result-card-title-wrap {
    margin-bottom: 20px;
}
.result-card-title {
    font-size: 24px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.4;
    letter-spacing: 0.5px;
}
.result-card-body {
    margin-bottom: 24px;
}
.result-card-body .result-box {
    white-space: pre-wrap;
    line-height: 2;
    font-size: 15px;
    color: var(--text-primary);
    border: none;
    background: transparent;
    padding: 0;
    border-radius: 0;
}
.result-card-tags-section {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 24px;
}
.result-tag {
    display: inline-block;
    background: rgba(212, 163, 115, 0.06);
    color: var(--text-muted);
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 12px;
    border: 1px solid rgba(255, 255, 255, 0.06);
}
.result-card-footer {
    display: flex;
    gap: 12px;
    justify-content: center;
    padding-top: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.btn-result-action {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--text-secondary);
    padding: 10px 24px;
    border-radius: 12px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    font-family: inherit;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}
.btn-result-action:hover {
    background: #D4A373;
    color: #121212;
    border-color: #D4A373;
}
@media (max-width: 600px) {
    .result-card { padding: 24px 18px; border-radius: 20px; }
    .result-card-title { font-size: 20px; }
    .result-card-footer { flex-direction: column; }
    .btn-result-action { width: 100%; justify-content: center; }
}

/* ===== 缓慢漂浮光晕 ===== */
@keyframes floatGlow {
    0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.3; }
    50% { transform: translate(30px, -20px) scale(1.1); opacity: 0.5; }
}
.hero::before {
    animation: floatGlow 20s ease-in-out infinite !important;
}
.hero::after {
    animation: floatGlow 20s ease-in-out infinite reverse !important;
}
'''

c = c.replace('</style>', new_css + '</style>')

# ==================== 7. 添加 shareCard 函数 ====================
# 在 copyText 函数后面加入
share_func = '''

function shareCard() {
    var titleEl = document.querySelector('.result-card-title');
    var bodyEl = document.getElementById('resultBox');
    var text = '';
    if (titleEl) text += titleEl.textContent.trim() + '\\n\\n';
    if (bodyEl) text += bodyEl.innerText;
    var shareText = '✦ 这段文字触动了我 ✦\\n\\n' + text.slice(0, 100) + '...\\n\\n—— 来自 InkFlow · 文字有温度';
    if (navigator.share) {
        navigator.share({ title: 'InkFlow', text: shareText }).catch(function() {});
    } else {
        navigator.clipboard.writeText(shareText).then(function() {
            showToast('✅ 已复制分享卡片，快去朋友圈分享吧');
        }).catch(function() {});
    }
}'''

# 在 showToast 后面插入
idx = c.find('</script>')
c = c[:idx] + share_func + c[idx:]

with open('templates/home.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Step 2 done: Hero + 情绪区 + 生成页 + 结果页")
