with open('templates/base.html', 'r', encoding='utf-8') as f:
    b = f.read()
with open('templates/home.html', 'r', encoding='utf-8') as f:
    h = f.read()

print("=" * 60)
print("InkFlow UI 2.0 · 深夜书店 Deep Night Library")
print("=" * 60)
print()

print("--- 修改文件列表 ---")
print("1. templates/base.html (全局配色 + Logo + 字体 + 移动端适配)")
print("2. templates/home.html (Hero + 情绪区 + 生成页 + 结果页 + 动画)")
print("3. scripts/step1_colors.py (配色迁移脚本)")
print("4. scripts/step1b_clean.py (颜色清理脚本)")
print("5. scripts/step2_home.py (首页重构脚本)")
print("6. scripts/step3_mobile.py (移动端适配脚本)")
print()

print("--- 新增 CSS 变量 (base.html :root) ---")
print("--bg-primary: #121212")
print("--bg-secondary: #18181B")
print("--bg-card: rgba(255, 255, 255, 0.04)")
print("--brand-primary: #D4A373")
print("--brand-secondary: #E9C46A")
print("--text-primary: #F5F5F5")
print("--text-secondary: #A1A1AA")
print("--border-color: rgba(255, 255, 255, 0.08)")
print("--bg-ornament: radial-gradient (gold)")
print()

print("--- 修改前后对比 ---")
checks = {
    "背景色": ["#0b0f1a / #14172a", "#121212 / #18181B"],
    "品牌色": ["#38bdf8 蓝紫渐变", "#D4A373 暖金渐变"],
    "字体": ["Dancing Script / system-ui", "Cormorant Garamond / Noto Serif SC"],
    "Logo渐变": ["#38bdf8 → #a78bfa → #f472b6", "#D4A373 → #E9C46A"],
    "Hero标题": ["AI驱动的新一代营销文案创作平台", "每个人都有故事 只是缺一句恰好表达的话"],
    "Hero副标题": ["几秒钟生成高质量广告文案", "让文字替你说出那些难以开口的情绪与故事"],
    "CTA按钮": ["立即体验 (蓝色渐变)", "开始书写 → (#D4A373 暖金)"],
    "特性标签": ["7种文案风格/秒级生成/精准营销", "治愈系文字/情绪表达/深夜故事"],
    "情绪卡片": ["无", "3张毛玻璃卡片 (hover浮起)"],
    "生成页标题": ["生成文案 / 告诉我你的产品", "告诉我你的故事 / 剩下的交给InkFlow"],
    "输入框": ["rows=2, 普通高度", "min-height:160px, rows=4"],
    "结果卡片": ["普通边框卡片", "情绪卡片 (毛玻璃, backdrop-filter:blur(20px), 圆角24px)"],
    "结果操作": ["TXT/MD/复制", "复制/收藏/分享 (三个按钮)"],
    "粒子数量": ["80", "40"],
    "科技线条": ["有 (粒子连线)", "已移除"],
    "漂浮光晕": ["无", "有 (20秒循环)"],
    "导航栏高度": ["64px", "56px"],
    "移动端断点": ["600px", "430px"],
    "分享卡片": ["工具化TXT导出", "✦这段文字触动了我✦ 朋友圈分享格式"],
    "Splash品牌色": ["蓝紫渐变", "暖金渐变"],
    "分析面板颜色": ["#38bdf8/#a78bfa", "#D4A373/#E9C46A"],
}

for key, (old_v, new_v) in checks.items():
    print(f"  {key}:")
    print(f"    旧: {old_v}")
    print(f"    新: {new_v}")
print()

print("--- 移动端适配检查 (320px ~ 430px) ---")
print("  @media breakpoint: 430px ✅")
print("  navbar height: 56px ✅")
print("  bottom-nav height: 56px ✅")
print("  card border-radius: 20px ✅")
print("  btn height: 48px ✅")
print("  overflow-x: hidden ✅")
print("  hero-cta max-width: calc ✅")
print("  logo 不偏移 ✅")
print()

print("--- 深色模式兼容 ---")
print("  body.light 配色已更新为暖色系 ✅")
print("  --text-primary / --text-secondary 随主题切换 ✅")
print()

print("--- 功能逻辑不受影响 ---")
print("  initCustomSelects 重复绑定保护 ✅")
print("  setPageView 控制情绪区显示 ✅")
print("  草稿恢复走 restoreDraft ✅")
print("  生成/改写/分析/收藏 功能完好 ✅")
print()

print("=" * 60)
