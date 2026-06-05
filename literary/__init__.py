"""
InkFlow 文学体系 - 核心模块
============================
8 个文学世界 × 意象库/句式库/模板/文章样本
支撑：每日摘录、创作生成、分享卡片
"""
import random
import json
import os
from datetime import datetime

# ============================
# 8 个文学世界
# ============================

WORLDS = [
    "youth",        # 少年感
    "unrequited",   # 爱而不得
    "nostalgia",    # 旧时光
    "lonely",       # 孤独宇宙
    "warmth",       # 人间烟火
    "romance",      # 浪漫诗篇
    "wildfire",     # 野火青春
    "mountains",    # 山海卷
]

WORLD_LABELS = {
    "youth": "少年感",
    "unrequited": "爱而不得",
    "nostalgia": "旧时光",
    "lonely": "孤独宇宙",
    "warmth": "人间烟火",
    "romance": "浪漫诗篇",
    "wildfire": "野火青春",
    "mountains": "山海卷",
}

WORLD_DESCRIPTIONS = {
    "youth": "夏天、校服、单车、走廊尽头的光。那些还没长大的日子。",
    "unrequited": "偷偷喜欢你，是我一个人的兵荒马乱。",
    "nostalgia": "我们怀念的不是那个年代，而是那个年代里还没走散的人。",
    "lonely": "城市很大，孤独也是。但孤独里藏着完整的自己。",
    "warmth": "人间烟火气，最抚凡人心。一碗面、一盏灯、一个等你回家的人。",
    "romance": "浪漫不是玫瑰和情话，是清晨的露水和黄昏的晚风都知道我爱你。",
    "wildfire": "青春是一场野火，烧过之后，留下的都是滚烫的回忆。",
    "mountains": "山在那里，海在那里，我们要去的地方，也在那里。",
}

# 情绪卡片 → 推荐世界映射
EMOTION_TO_WORLDS = {
    "miss": ["youth", "nostalgia", "unrequited"],
    "regret": ["nostalgia", "unrequited", "lonely"],
    "heartfelt": ["warmth", "romance", "lonely"],
    "comfort": ["warmth", "lonely", "mountains"],
    "story": ["youth", "wildfire", "nostalgia"],
    "moment": ["romance", "warmth", "wildfire"],
    "chat": ["warmth", "lonely", "youth"],
}

# ============================
# 加载文学世界数据
# ============================

_world_data_cache = {}

def load_world(world_id):
    """加载某个文学世界的完整数据"""
    if world_id in _world_data_cache:
        return _world_data_cache[world_id]
    
    module_path = f"literary.worlds.{world_id}"
    try:
        import importlib
        mod = importlib.import_module(module_path)
        data = {
            "images": getattr(mod, "IMAGES", []),
            "phrases": getattr(mod, "PHRASES", []),
            "openings": getattr(mod, "OPENINGS", []),
            "closings": getattr(mod, "CLOSINGS", []),
            "samples": getattr(mod, "SAMPLES", []),
        }
        _world_data_cache[world_id] = data
        return data
    except Exception as e:
        print(f"加载文学世界 {world_id} 失败: {e}")
        return {"images": [], "phrases": [], "openings": [], "closings": [], "samples": []}

# ============================
# 短篇生成器
# ============================

def generate_short_text(world_id=None, emotion_id=None, seed_words="", length="short"):
    """
    生成一篇短文
    - world_id: 指定文学世界
    - emotion_id: 情绪入口，自动映射世界
    - seed_words: 用户输入的关键词
    - length: short(80-150字) / medium(150-250字) / long(250-400字)
    """
    # 选择世界
    if not world_id and emotion_id:
        candidates = EMOTION_TO_WORLDS.get(emotion_id, list(WORLDS))
        world_id = random.choice(candidates)
    elif not world_id:
        world_id = random.choice(WORLDS)
    
    data = load_world(world_id)
    if not data["images"]:
        return {"title": "", "content": "文学世界加载中...", "world": world_id}
    
    # 选择意象和句子
    images = random.sample(data["images"], min(5, len(data["images"])))
    phrase = random.choice(data["phrases"]) if data["phrases"] else ""
    opening = random.choice(data["openings"]) if data["openings"] else ""
    closing = random.choice(data["closings"]) if data["closings"] else ""
    
    # 组装正文（文学45% / 画面35% / 情绪20%）
    paragraphs = []
    
    # 开头
    if opening:
        paragraphs.append(opening)
    
    # 核心段 - 用意象构建画面
    core_images = images[:3]
    scene = "。".join(core_images) + "。"
    if phrase:
        scene += "\n\n" + phrase
    paragraphs.append(scene)
    
    # 情绪段
    if len(images) > 3:
        emotion_part = images[3] + "。那一刻，"
        emotion_part += random.choice([
            "心里有个地方被轻轻碰了一下。",
            "世界突然安静了下来。",
            "好像所有的语言都变得多余。",
            "我知道，这个瞬间会记很久。",
            "风刚好吹过来，像是听懂了什么。",
        ])
        paragraphs.append(emotion_part)
    
    # 结尾
    if closing:
        paragraphs.append(closing)
    elif len(images) > 4:
        ending = images[4] + "。"
        ending += random.choice([
            "这样就很好。",
            "后来我才明白，这就是生活。",
            "有些事，不说出来也是一种表达。",
            "时间会带走很多，也会留下一些。",
            "大概，这就是我想说的全部了。",
        ])
        paragraphs.append(ending)
    
    content = "\n\n".join(paragraphs)
    
    # 截取长度
    target_len = {"short": 150, "medium": 250, "long": 400}.get(length, 150)
    if len(content) > target_len:
        lines = content.split("\n\n")
        result = []
        total = 0
        for line in lines:
            if total + len(line) > target_len:
                break
            result.append(line)
            total += len(line)
        if len(result) < len(lines):
            result.append(lines[-1])  # 至少保留结尾
        content = "\n\n".join(result)
    
    # 生成标题
    title = generate_title(world_id, images)
    
    return {
        "title": title,
        "content": content,
        "world_id": world_id,
        "world_label": WORLD_LABELS.get(world_id, world_id),
    }


def generate_title(world_id, images=None):
    """生成标题"""
    if not images:
        images = []
    templates = [
        f"关于{random.choice(['那些', '一些', '某个'])}{random.choice(images[:3] if images else ['瞬间'])}",
        f"{random.choice(images[:2] if images else ['某天'])}",
        f"{random.choice(['你', '我', '我们'])}和{random.choice(images[:2] if images else ['时间'])}",
        f"{random.choice(images[:1] if images else ['晚风'])}",
        f"{random.choice(['后来', '以前', '现在'])}的{random.choice(images[:3] if images else ['我们'])}",
    ]
    return random.choice(templates)


# ============================
# 每日摘录模块
# ============================

DAILY_LIMIT = 10  # 每日最多推送条数


def get_daily_pick(user_id=None, interests=None, max_count=5):
    """
    获取每日精选摘录
    - 按兴趣/文学世界推荐
    - 每日固定
    """
    today = datetime.now().strftime("%Y-%m-%d")
    random.seed(today + str(user_id or ""))
    
    picks = []
    worlds_to_use = interests if interests else WORLDS
    
    # 从文学世界的样本中选取
    for world_id in worlds_to_use[:max_count]:
        data = load_world(world_id)
        samples = data.get("samples", [])
        if samples:
            sample = random.choice(samples)
            picks.append({
                "id": f"{today}_{world_id}_{random.randint(100,999)}",
                "world_id": world_id,
                "world_label": WORLD_LABELS.get(world_id, world_id),
                "title": sample.get("title", ""),
                "content": sample.get("content", ""),
                "author": sample.get("author", ""),
                "source": sample.get("source", ""),
                "date": today,
            })
    
    # 如果样本不够，用生成器补充
    while len(picks) < max_count:
        world_id = random.choice(WORLDS)
        gen = generate_short_text(world_id=world_id, length="short")
        picks.append({
            "id": f"{today}_gen_{random.randint(100,999)}",
            "world_id": world_id,
            "world_label": WORLD_LABELS.get(world_id, world_id),
            "title": gen["title"],
            "content": gen["content"],
            "author": "InkFlow 灵笔",
            "source": "文学世界 · " + WORLD_LABELS.get(world_id, world_id),
            "date": today,
            "is_generated": True,
        })
    
    return picks[:max_count]


def get_daily_detail(pick_id):
    """获取单条摘录详情（含相关推荐和创作入口）"""
    parts = pick_id.split("_")
    if len(parts) >= 2:
        world_id = parts[1]
        data = load_world(world_id)
        related_worlds = [w for w in WORLDS if w != world_id][:3]
        return {
            "world_id": world_id,
            "world_label": WORLD_LABELS.get(world_id, world_id),
            "related_worlds": [(w, WORLD_LABELS.get(w, w)) for w in related_worlds],
        }
    return {}


# ============================
# 每日摘录存储（简化版，后续可接入数据库）
# ============================

_user_daily_picks = {}  # user_id -> [pick_ids]

def mark_user_read(user_id, pick_id):
    """标记用户已读"""
    if user_id not in _user_daily_picks:
        _user_daily_picks[user_id] = set()
    _user_daily_picks[user_id].add(pick_id)


def get_user_reads(user_id):
    return _user_daily_picks.get(user_id, set())
