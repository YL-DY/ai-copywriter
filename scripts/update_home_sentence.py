# -*- coding: utf-8 -*-
"""更新 home.html 的今日句子部分：CSS + HTML + JS"""
import re

path = "d:/projects/ai-copywriter/templates/home.html"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# ===== 1. CSS: 在 </style> 前插入新样式 =====
new_css = '''
/* ===== 今日句子动态版 ===== */
.sentence-atmosphere {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    border-radius: 20px;
    transition: background 1.2s ease;
    pointer-events: none;
    z-index: 0;
}
.emotion-card-single {
    position: relative;
    overflow: hidden;
}
.emotion-card-single .emotion-card-icon,
.emotion-card-single .emotion-card-text,
.emotion-card-single .emotion-card-divider,
.emotion-card-single .emotion-card-author,
.sentence-actions,
.sentence-source {
    position: relative;
    z-index: 1;
}
.sentence-typewriter {
    display: inline;
    white-space: pre-line;
    font-size: 15px;
    line-height: 1.9;
    color: var(--text-primary);
}
.sentence-typewriter .cursor {
    display: inline-block;
    width: 2px;
    height: 1em;
    background: #D4A373;
    margin-left: 2px;
    vertical-align: text-bottom;
    animation: cursorBlink 0.8s step-end infinite;
}
@keyframes cursorBlink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}
.sentence-actions {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-top: 20px;
}
.sentence-btn {
    padding: 8px 20px;
    border-radius: 20px;
    border: 1px solid rgba(212, 163, 115, 0.25);
    background: rgba(212, 163, 115, 0.06);
    color: var(--text-muted);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.25s;
}
.sentence-btn:hover {
    background: rgba(212, 163, 115, 0.12);
    color: #D4A373;
    border-color: #D4A373;
}
.sentence-btn.active {
    background: rgba(212, 163, 115, 0.15);
    border-color: #D4A373;
    color: #D4A373;
}
.sentence-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}
.sentence-loading {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid rgba(212, 163, 115, 0.2);
    border-top-color: #D4A373;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    vertical-align: middle;
    margin-right: 6px;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}
.sentence-source {
    text-align: center;
    font-size: 13px;
    color: var(--text-muted);
    margin-top: 4px;
    font-style: italic;
}
.hot-ranking {
    max-width: 520px;
    margin: 24px auto 0;
    padding: 16px 20px;
    background: rgba(11, 15, 26, 0.3);
    border-radius: 16px;
    border: 1px solid rgba(51, 65, 85, 0.15);
}
.hot-ranking-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 12px;
    text-align: center;
}
.hot-ranking-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
    border-bottom: 1px solid rgba(51, 65, 85, 0.08);
}
.hot-ranking-item:last-child {
    border-bottom: none;
}
.hot-ranking-rank {
    font-size: 14px;
    font-weight: 700;
    color: #D4A373;
    min-width: 24px;
    text-align: center;
}
.hot-ranking-text {
    flex: 1;
    font-size: 13px;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.hot-ranking-count {
    font-size: 12px;
    color: var(--text-muted);
    white-space: nowrap;
}
@media (max-width: 600px) {
    .sentence-typewriter { font-size: 14px; }
    .sentence-actions { gap: 8px; }
    .sentence-btn { padding: 6px 14px; font-size: 12px; }
    .hot-ranking { margin: 16px 12px 0; padding: 12px 14px; }
}
'''

# 在 </style> 前插入
content = content.replace('</style>', new_css + '\n</style>', 1)

# ===== 2. HTML: 替换静态句子区为动态版本 =====
old_html = '''<div class="emotion-section" id="emotionSection">
    <h2 class="emotion-title">今日句子</h2>
    <div class="emotion-cards">
        <div class="emotion-card emotion-card-single">
            <div class="emotion-card-icon">📖</div>
            <div class="emotion-card-text">"{{ random_sentence }}"</div>
            <div class="emotion-card-divider"></div>
            <div class="emotion-card-author">—— InkFlow · 每日一句</div>
        </div>
    </div>
</div>'''

new_html = '''<div class="emotion-section" id="emotionSection">
    <h2 class="emotion-title">今日句子</h2>
    <div class="emotion-cards">
        <div class="emotion-card emotion-card-single" id="sentenceCard">
            <div class="sentence-atmosphere" id="sentenceAtmo"></div>
            <div class="emotion-card-icon">📖</div>
            <div class="sentence-typewriter" id="sentenceText">
                <span class="cursor"></span>
            </div>
            <div class="emotion-card-divider"></div>
            <div class="sentence-source" id="sentenceSource"></div>
            <div class="sentence-actions">
                <button class="sentence-btn" id="sentenceNextBtn" onclick="loadNextSentence()">⟳ 换一句</button>
                <button class="sentence-btn" id="sentenceFavBtn" onclick="toggleSentenceFav()">♡ 收藏</button>
            </div>
        </div>
    </div>
    <div class="hot-ranking" id="hotRanking" style="display:none;">
        <div class="hot-ranking-title">🔥 热门摘录</div>
        <div id="hotRankingList"></div>
    </div>
</div>'''

if old_html in content:
    content = content.replace(old_html, new_html, 1)
    print("HTML section replaced successfully!")
else:
    print("WARNING: Old HTML not found! Trying fuzzy match...")
    # Try to find the section by partial match
    import re
    pattern = r'<div class="emotion-section" id="emotionSection">.*?</div>\s*</div>\s*</div>'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print(f"Found emotion section at position {match.start()}-{match.end()}")
        content = content[:match.start()] + new_html + content[match.end():]
        print("HTML section replaced via regex!")
    else:
        print("ERROR: Could not find emotion section at all!")

# ===== 3. JavaScript: 在最后一个 </script> 前插入新函数 =====
new_js = '''
// ===== 今日句子动态功能 =====
var currentSentence = null;
var isFaved = false;
var sentenceLoading = false;

function loadNextSentence() {
    if (sentenceLoading) return;
    sentenceLoading = true;
    var btn = document.getElementById('sentenceNextBtn');
    var favBtn = document.getElementById('sentenceFavBtn');
    if (btn) btn.disabled = true;
    if (favBtn) { favBtn.classList.remove('active'); favBtn.textContent = '♡ 收藏'; }
    isFaved = false;
    var textEl = document.getElementById('sentenceText');
    if (textEl) textEl.innerHTML = '<span class="sentence-loading"></span> 加载中...';
    fetch('/api/today-sentence')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.ok) {
                currentSentence = data;
                typewriteSentence(data.text, document.getElementById('sentenceText'));
                var srcEl = document.getElementById('sentenceSource');
                if (srcEl) srcEl.textContent = data.source || '';
                updateSentenceAtmosphere(data.text);
            } else {
                if (textEl) textEl.textContent = '暂时没有句子，请稍后再来';
            }
        })
        .catch(function() {
            if (textEl) textEl.textContent = '加载失败，请重试';
        })
        .finally(function() {
            sentenceLoading = false;
            if (btn) btn.disabled = false;
        });
}

function typewriteSentence(text, container) {
    if (!container) return;
    container.innerHTML = '';
    var i = 0;
    var cursorSpan = document.createElement('span');
    cursorSpan.className = 'cursor';
    function addChar() {
        if (i < text.length) {
            var char = text.charAt(i);
            if (char === '\\n') {
                container.appendChild(document.createElement('br'));
            } else {
                var span = document.createElement('span');
                span.textContent = char;
                container.appendChild(span);
            }
            i++;
            setTimeout(addChar, 30 + Math.random() * 20);
        } else {
            container.appendChild(cursorSpan);
        }
    }
    addChar();
}

function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function updateSentenceAtmosphere(text) {
    var atmo = document.getElementById('sentenceAtmo');
    if (!atmo) return;
    var len = text.length;
    var bg;
    if (len < 30) {
        bg = 'radial-gradient(ellipse at center, rgba(212,163,115,0.08) 0%, transparent 70%)';
    } else if (len < 100) {
        bg = 'radial-gradient(ellipse at center, rgba(99,102,241,0.06) 0%, rgba(139,92,246,0.04) 40%, transparent 70%)';
    } else {
        bg = 'radial-gradient(ellipse at center, rgba(13,148,136,0.06) 0%, rgba(56,189,248,0.04) 40%, transparent 70%)';
    }
    // Check keywords
    var lower = text.toLowerCase();
    if (/[\\u96e8\\u6cea\\u51b7]/.test(lower)) {
        bg = 'radial-gradient(ellipse at center, rgba(56,189,248,0.08) 0%, transparent 70%)';
    } else if (/[\\u6696\\u5149\\u6625\\u9633]/.test(lower)) {
        bg = 'radial-gradient(ellipse at center, rgba(251,191,36,0.08) 0%, transparent 70%)';
    } else if (/[\\u591c\\u68a6\\u661f\\u6708]/.test(lower)) {
        bg = 'radial-gradient(ellipse at center, rgba(99,102,241,0.08) 0%, rgba(15,23,42,0.3) 50%, transparent 70%)';
    }
    atmo.style.background = bg;
}

function toggleSentenceFav() {
    if (!currentSentence) return;
    var btn = document.getElementById('sentenceFavBtn');
    if (!btn) return;
    btn.disabled = true;
    fetch('/api/today-sentence/fav', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            text: currentSentence.text,
            author: currentSentence.author,
            style: currentSentence.style,
            history_id: currentSentence.history_id
        })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.ok) {
            isFaved = data.faved;
            btn.textContent = isFaved ? '♥ 已收藏' : '♡ 收藏';
            if (isFaved) {
                btn.classList.add('active');
                showToast('✅ 已收藏');
                loadHotRanking();
            } else {
                btn.classList.remove('active');
                showToast('已取消收藏');
                loadHotRanking();
            }
        }
    })
    .catch(function() {
        showToast('❌ 操作失败');
    })
    .finally(function() {
        btn.disabled = false;
    });
}

function loadHotRanking() {
    fetch('/api/today-sentence/hot')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var container = document.getElementById('hotRanking');
            var list = document.getElementById('hotRankingList');
            if (!container || !list) return;
            if (data.ok && data.items && data.items.length > 0) {
                container.style.display = 'block';
                list.innerHTML = '';
                data.items.forEach(function(item, idx) {
                    var div = document.createElement('div');
                    div.className = 'hot-ranking-item';
                    var rank = (idx + 1) <= 3 ? ['🥇','🥈','🥉'][idx] : (idx + 1);
                    div.innerHTML = '<span class="hot-ranking-rank">' + rank + '</span>' +
                        '<span class="hot-ranking-text">' + escapeHtml(item.text) + '</span>' +
                        '<span class="hot-ranking-count">' + item.fav_count + ' 收藏</span>';
                    list.appendChild(div);
                });
            } else {
                container.style.display = 'none';
            }
        })
        .catch(function() {});
}

// Auto-load on DOMContentLoaded after splash
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        loadNextSentence();
        loadHotRanking();
    }, 3000);
});
'''

# 在最后一个 </script> 前插入
last_script_end = content.rfind('</script>')
if last_script_end != -1:
    content = content[:last_script_end] + new_js + '\n' + content[last_script_end:]
    print("JS inserted successfully!")
else:
    print("ERROR: Could not find </script>!")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done! home.html updated successfully.")
