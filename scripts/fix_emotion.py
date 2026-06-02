with open('templates/home.html', 'r', encoding='utf-8') as f:
    h = f.read()

# 在 setPageView 中添加情绪区控制
old_js = '''function setPageView(view) {
    var heroPage = document.getElementById('heroPage');
    var generatePage = document.getElementById('generatePage');
    if (!heroPage || !generatePage) return;

    if (view === 'generate') {
        heroPage.style.display = 'none';
        generatePage.style.display = 'block';

    } else {
        heroPage.style.display = 'flex';
        generatePage.style.display = 'none';
    }
}'''

new_js = '''function setPageView(view) {
    var heroPage = document.getElementById('heroPage');
    var generatePage = document.getElementById('generatePage');
    var emotionSection = document.getElementById('emotionSection');
    if (!heroPage || !generatePage) return;

    if (view === 'generate') {
        heroPage.style.display = 'none';
        generatePage.style.display = 'block';
        if (emotionSection) emotionSection.style.display = 'none';
    } else {
        heroPage.style.display = 'flex';
        generatePage.style.display = 'none';
        if (emotionSection) emotionSection.style.display = 'block';
    }
}'''

h = h.replace(old_js, new_js)

# 同时修改底部 tab 的点击处理，也用 setPageView，避免直接操作 style
old_tab = '''            if (window.setPageView) {
                window.setPageView('generate');
            } else {
                var heroPage = document.getElementById('heroPage');
                var genPage = document.getElementById('generatePage');
                if (heroPage) heroPage.style.display = 'none';
                if (genPage) genPage.style.display = 'block';
            }'''

new_tab = '''            if (window.setPageView) {
                window.setPageView('generate');
            } else {
                var heroPage = document.getElementById('heroPage');
                var genPage = document.getElementById('generatePage');
                var emotionSection = document.getElementById('emotionSection');
                if (heroPage) heroPage.style.display = 'none';
                if (genPage) genPage.style.display = 'block';
                if (emotionSection) emotionSection.style.display = 'none';
            }'''

h = h.replace(old_tab, new_tab)

with open('templates/home.html', 'w', encoding='utf-8') as f:
    f.write(h)

print("OK - emotion section visibility controlled via setPageView")
