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

# 加载扩展数据（JSON 补充文件）
_expansion_data = None
def _get_expansion():
    global _expansion_data
    if _expansion_data is not None:
        return _expansion_data
    json_path = os.path.join(os.path.dirname(__file__), "expansion_data.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                _expansion_data = json.load(f)
        except Exception:
            _expansion_data = {}
    else:
        _expansion_data = {}
    return _expansion_data


def load_world(world_id):
    """加载某个文学世界的完整数据（含扩展数据）"""
    if world_id in _world_data_cache:
        return _world_data_cache[world_id]
    
    module_path = f"literary.worlds.{world_id}"
    try:
        import importlib
        mod = importlib.import_module(module_path)
        data = {
            "images": list(getattr(mod, "IMAGES", [])),
            "phrases": list(getattr(mod, "PHRASES", [])),
            "openings": list(getattr(mod, "OPENINGS", [])),
            "closings": list(getattr(mod, "CLOSINGS", [])),
            "samples": list(getattr(mod, "SAMPLES", [])),
        }
        
        # 合并扩展数据
        expansion = _get_expansion()
        if world_id in expansion:
            ext = expansion[world_id]
            for key in ["images", "phrases", "openings", "closings"]:
                if key in ext and isinstance(ext[key], list):
                    existing = data.get(key, [])
                    # 去重合并（用集合去重）
                    existing_set = set(existing)
                    for item in ext[key]:
                        if item not in existing_set:
                            existing.append(item)
                            existing_set.add(item)
                    data[key] = existing
        
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


# ============================
# 8 种文学风格库（v2 升级）
# ============================

STYLES = [
    "modern_poetry",      # 现代诗
    "white_space",        # 留白文学
    "youth_campus",       # 青春校园
    "regret_lit",         # 遗憾文学
    "healing_lit",        # 治愈文学
    "late_night",         # 深夜情绪
    "short_sentence",     # 高级短句
    "viral_essay",        # 网感文学
]

STYLE_LABELS = {
    "modern_poetry": "现代诗",
    "white_space": "留白文学",
    "youth_campus": "青春校园",
    "regret_lit": "遗憾文学",
    "healing_lit": "治愈文学",
    "late_night": "深夜情绪",
    "short_sentence": "高级短句",
    "viral_essay": "网感文学",
}

STYLE_DESCRIPTIONS = {
    "modern_poetry": "大量换行、意象堆叠、不解释。用画面和节奏代替叙述。",
    "white_space": "字数极少、留白极多。一句话就是一个世界。",
    "youth_campus": "上课铃、操场、走廊、课桌、暗恋。那些回不去的校园时光。",
    "regret_lit": "错过、来不及、如果当初。遗憾是最长情的告白。",
    "healing_lit": "温柔、希望、与自己和解。给疲惫的心一个拥抱。",
    "late_night": "凌晨、独处、克制地表达。深夜的情绪最真实。",
    "short_sentence": "字数极少、密度极高。一句顶一万句。",
    "viral_essay": "口语化、有共鸣、有网感。像深夜刷到的一条动态。",
}

# ============================
# 自动混合模式配置
# ============================

AUTO_MIX_CONFIG = {
    "enabled": True,
    "weights": {
        "modern_poetry": 0.30,
        "white_space": 0.20,
        "youth_campus": 0.20,
        "regret_lit": 0.15,
        "healing_lit": 0.15,
        "late_night": 0.0,
        "short_sentence": 0.0,
        "viral_essay": 0.0,
    }
}


# ============================
# 风格生成器 - 意象/句式库
# ============================

# --- 现代诗 ---
_MODERN_POETRY_IMAGES = [
    "月光把影子拉得很长很长", "风穿过空荡荡的走廊", "路灯下站着一个人",
    "雨打在窗玻璃上 又滑落", "烟灰缸里堆满未说的话", "凌晨三点的街道 只有便利店还亮着",
    "树叶在风里翻了个身", "黄昏把天空染成旧照片的颜色", "一只鸟停在电线杆上 像省略号",
    "地铁穿过黑暗 又回到光明", "咖啡凉了 故事还没讲完", "窗帘被风吹起 像在招手",
    "影子在墙上慢慢变淡", "雨停了 但屋檐还在滴水", "路灯把雨丝照得像银线",
    "风吹过树梢 发出海浪的声音", "月亮躲在云后面 只露出一半", "烟圈在空气中慢慢散开",
]

_MODERN_POETRY_LINES = [
    "有些话 说了就轻了", "沉默 是今晚的答案", "你不在 日子照常过",
    "只是偶尔 会停下来", "像等一场不会来的雨", "我们都在学着告别",
    "用一辈子的时间", "有些人 适合放在回忆里", "像旧书签 夹在某一页",
    "偶尔翻到 会心一笑", "然后 继续往前", "时间是个哑巴 什么也不说",
    "但什么都改变了", "我们终将 成为别人的故事", "而故事 总有结局",
    "不是所有的花 都会开", "不是所有的等待 都有答案", "但风会记得 你来过",
]

# --- 留白文学 ---
_WHITE_SPACE_LINES = [
    "后来。\n\n我们。\n\n没有后来。",
    "你问我遗憾吗。\n\n我笑了笑。\n\n没说话。",
    "有些人。\n\n遇见就够了。\n\n余生就算了。",
    "我们之间。\n\n隔着一整个青春。\n\n回不去的那种。",
    "故事不长。\n\n也不难讲。\n\n相识一场。\n\n爱而不得。",
    "我等你。\n\n很久。\n\n久到忘了时间。\n\n然后。\n\n我走了。",
    "你说。\n\n改天。\n\n后来我才明白。\n\n改天是最大的谎言。",
    "我们。\n\n就这样。\n\n散了吧。",
    "有些路。\n\n只能一个人走。\n\n不是不想回头。\n\n是回不了头。",
    "你是我。\n\n做过最美的梦。\n\n可惜。\n\n天总会亮。",
    "我以为。\n\n只要很认真地喜欢。\n\n就可以打动一个人。\n\n原来。\n\n只是打动了我自己。",
    "我们之间。\n\n最近的距离。\n\n是点赞。\n\n最远的距离。\n\n也是点赞。",
    "删掉了。\n\n又加回来。\n\n反反复复。\n\n最后。\n\n还是删了。",
    "那天。\n\n阳光很好。\n\n你穿了一件白衬衫。\n\n后来。\n\n我再也没见过那样的阳光。",
    "有些话。\n\n到嘴边。\n\n又咽回去了。\n\n不是不想说。\n\n是说了也没用。",
]

# --- 青春校园 ---
_YOUTH_IMAGES = [
    "上课铃响了 走廊里奔跑的身影", "课桌上刻着的名字 已经模糊了",
    "操场上的夕阳 把影子拉得很长", "教室后排的座位 总是靠窗",
    "校服袖口上 画着小小的涂鸦", "食堂里排着长长的队 有说有笑",
    "考试时偷偷传的小纸条", "放学后空荡荡的教室 只有风扇在转",
    "篮球场上的汗水 和呐喊声", "图书馆里 阳光透过书架洒下来",
    "黑板上的倒计时 一天天减少", "宿舍熄灯后的悄悄话",
    "那个总在走廊尽头出现的背影", "毕业照上 大家都笑得很开心",
    "校门口的小卖部 五毛钱的辣条", "下雨天 有人把伞递给你",
]

_YOUTH_PHRASES = [
    "那时候 我们以为日子很长 长到可以挥霍",
    "后来才明白 青春是一场来不及告别的远行",
    "那个夏天 风很轻 天很蓝 你刚好在",
    "我们笑着说再见 却不知道 有些人真的再也不见",
    "青春是一本太仓促的书 我们含着泪 一读再读",
    "那时候 喜欢一个人 就是偷偷多看他几眼",
    "后来 我们去了不同的城市 看了不同的风景",
    "但偶尔 还是会想起 那个教室 那个座位 那个人",
    "青春是一场大雨 即使感冒了 也想再淋一次",
    "那些年 我们以为的永远 其实只是夏天",
]

# --- 遗憾文学 ---
_REGRET_IMAGES = [
    "旧照片已经泛黄 但记忆还很清晰", "车站的广播响了 车开走了 你没来",
    "手机里 还存着没发出去的消息", "那个说了再见的人 真的再也没见",
    "衣柜里 还挂着那件没送出去的礼物", "聊天记录停在某一天 再也没有更新",
    "路过那家店 还是会下意识地放慢脚步", "梦里 你还是原来的样子",
    "有些话 当时没说 后来就没机会了", "如果当时 我勇敢一点 结局会不会不一样",
    "你教会了我很多 唯独没教会我忘记", "时间没有等我 是你忘了带我走",
]

_REGRET_PHRASES = [
    "最遗憾的不是得不到 而是差一点",
    "我们最大的默契 是我不找你 你也不找我",
    "后来我终于知道 有些人 错过就是一辈子",
    "如果重来一次 我还是会选择认识你 虽然结局很遗憾",
    "你是我藏在手机里的秘密 也是我放在心底的遗憾",
    "有些路 不走不甘心 走了 一身伤",
    "我还在等你 但我知道 你不会来了",
    "故事的开头总是极尽温柔 结局却配不上整个开头",
]

# --- 治愈文学 ---
_HEALING_IMAGES = [
    "阳光透过窗帘 洒在地板上 暖暖的", "一杯热茶 一本书 一个安静的下午",
    "窗台上的绿植 又长出了新芽", "雨停了 天边出现了一道彩虹",
    "被子晒过太阳的味道 让人安心", "猫在脚边打呼噜 时间慢了下来",
    "耳机里放着一首老歌 旋律温柔", "傍晚的风 吹在脸上 软软的",
    "路灯亮起来的时候 有人在等你回家", "冰箱里 还有半块蛋糕 和明天的期待",
    "朋友发来一条消息 说 想你了", "洗完热水澡 钻进被窝的那一刻",
    "春天来了 路边的花都开了", "陌生人的一个微笑 可以暖一整天",
]

_HEALING_PHRASES = [
    "没关系 慢慢来 你又不差",
    "你已经很棒了 只是还没遇到那个懂你的人",
    "生活不会一直糟糕 就像雨总会停 天总会晴",
    "你要相信 这个世界上 总有人在偷偷爱着你",
    "累了就休息 不用一直坚强",
    "今天的你辛苦了 好好睡一觉 明天又是新的一天",
    "你值得被温柔对待 包括被自己温柔对待",
    "有些路 一个人走 也会看到不一样的风景",
    "别急 时间会给你最好的答案",
    "你已经做得很好了 剩下的 交给时间",
]

# --- 深夜情绪 ---
_LATE_NIGHT_IMAGES = [
    "凌晨两点 窗外只有风声", "手机屏幕的光 照亮了半边脸",
    "翻来覆去 睡不着 也不知道在想什么", "朋友圈刷了一遍又一遍 没有更新",
    "打开对话框 打了又删 删了又打", "窗外的路灯 亮了一整夜",
    "耳机里的歌 循环了一百遍", "冰箱里 只剩下一瓶矿泉水",
    "翻到一张旧照片 愣了很久", "想找个人说说话 发现不知道找谁",
    "天亮的时候 才迷迷糊糊睡着", "做了一个梦 醒来就忘了",
    "凌晨四点的街道 安静得像另一个世界", "烟灰缸里 多了几个烟头",
]

_LATE_NIGHT_PHRASES = [
    "深夜是情绪的放大镜 白天藏起来的 晚上都会跑出来",
    "不是不困 是不想结束这一天 因为明天还要继续",
    "白天是搞笑废物 晚上是抑郁怪物",
    "深夜适合想念 也适合遗忘",
    "有些话 只敢在深夜说给自己听",
    "凌晨的清醒 是对白天的报复",
    "黑夜给了我黑色的眼睛 我却用它来熬夜",
    "深夜不睡觉的人 心里都住着一个不可能的人",
]

# --- 高级短句 ---
_SHORT_SENTENCES = [
    "后来 你成了别人的故事。",
    "我没事 只是习惯了逞强。",
    "有些人 光是遇见 就已经是上上签了。",
    "你是我 做过最美的梦 可惜天总会亮。",
    "我们之间 隔着一条叫「如果」的河。",
    "时间没有治愈我 只是教会了我习惯。",
    "你是我 写在备忘录里的秘密。",
    "有些人 适合放在心里 不适合在一起。",
    "我还在等 等一个不可能的可能。",
    "你是我 青春里最大的遗憾。",
    "我们 终究 还是 走散了。",
    "有些爱 只能止于唇齿 掩于岁月。",
    "你是我 想见 却见不到的人。",
    "故事我忘了 但你我还记得。",
    "我很好 只是偶尔会想起你。",
    "有些人 不说再见 就再也不见了。",
    "你是我 藏在手机里的秘密。",
    "后来 我们什么都有了 却没有了我们。",
    "我学会了告别 却学不会忘记。",
    "你是我 青春里最温柔的遗憾。",
]

# --- 网感文学 ---
_VIRAL_TOPICS = [
    "你有没有发现 长大后 我们都学会了沉默",
    "今天在地铁上 看到一个女孩 哭得很克制",
    "其实我们都知道 有些人 这辈子不会再见了",
    "成年人的崩溃 是从「没事」开始的",
    "你有没有一个 想见却见不到的人",
    "今天翻到以前的聊天记录 笑着笑着就沉默了",
    "其实不是忘不掉 只是不想忘",
    "你有没有 突然就哭了的时候 没有原因",
    "后来才明白 真正的告别 是没有告别的",
    "今天看到一句话 瞬间破防了",
    "你有没有 在深夜 特别想找一个人说说话",
    "其实我们怀念的 不是那个人 而是那个奋不顾身的自己",
    "今天路过一家店 听到一首歌 愣在原地",
    "你有没有 一个想删又舍不得删的人",
    "其实我们都知道 答案 只是不想承认",
]

_VIRAL_ENDINGS = [
    "你呢 有没有一个 想忘忘不掉的人？",
    "所以啊 有些人 遇见就够了 余生就算了。",
    "大概 这就是成长吧 学会接受 学会放下。",
    "你呢 最近还好吗？",
    "所以 好好爱自己 比什么都重要。",
    "你呢 有没有一个 藏在心底的名字？",
    "所以啊 珍惜眼前人 因为有些人 一转身就是一辈子。",
    "你呢 是不是也有一个 想见却见不到的人？",
]


# ============================
# 风格生成器函数
# ============================

def _gen_modern_poetry(seed_words="", length="short"):
    """现代诗生成器：大量换行、意象堆叠、不解释"""
    images = random.sample(_MODERN_POETRY_IMAGES, min(6, len(_MODERN_POETRY_IMAGES)))
    lines = random.sample(_MODERN_POETRY_LINES, min(4, len(_MODERN_POETRY_LINES)))
    
    stanzas = []
    
    # 第一段：2-3 个意象
    stanza1 = "\n".join(images[:3])
    stanzas.append(stanza1)
    
    # 第二段：1-2 句诗行
    stanza2 = "\n".join(lines[:2])
    stanzas.append(stanza2)
    
    # 第三段：剩余意象 + 诗行
    remaining = images[3:5] + lines[2:4]
    stanza3 = "\n".join(remaining)
    stanzas.append(stanza3)
    
    if seed_words:
        # 把用户输入融入
        stanzas.insert(1, seed_words)
    
    content = "\n\n".join(stanzas)
    
    # 生成标题
    title_templates = [
        f"《{random.choice(images)[:6]}》",
        f"《{random.choice(['今夜', '某天', '后来', '此刻'])}》",
        f"《无题》",
    ]
    title = random.choice(title_templates)
    
    return {"title": title, "content": content, "style_id": "modern_poetry", "style_label": "现代诗"}


def _gen_white_space(seed_words="", length="short"):
    """留白文学生成器：极简、一句话一段、大量留白"""
    lines = random.sample(_WHITE_SPACE_LINES, min(3, len(_WHITE_SPACE_LINES)))
    
    if seed_words:
        # 把用户输入作为开头
        seed_lines = seed_words.split("\n")
        content = "\n\n".join(seed_lines + lines)
    else:
        content = "\n\n".join(lines)
    
    title_templates = [
        f"《{random.choice(['后来', '我们', '有些人', '故事', '如果'])}》",
        f"《{random.choice(['遗憾', '错过', '遇见', '告别', '沉默'])}》",
    ]
    title = random.choice(title_templates)
    
    return {"title": title, "content": content, "style_id": "white_space", "style_label": "留白文学"}


def _gen_youth_campus(seed_words="", length="short"):
    """青春校园生成器：校园场景叙事"""
    images = random.sample(_YOUTH_IMAGES, min(4, len(_YOUTH_IMAGES)))
    phrases = random.sample(_YOUTH_PHRASES, min(3, len(_YOUTH_PHRASES)))
    
    paragraphs = []
    
    # 开头：场景描写
    opening = images[0] + "。"
    paragraphs.append(opening)
    
    # 中间：意象 + 感悟
    mid = images[1] + "。\n" + phrases[0]
    paragraphs.append(mid)
    
    # 结尾：回忆式收束
    ending = phrases[1] + "\n" + images[2] + "。\n" + phrases[2]
    paragraphs.append(ending)
    
    if seed_words:
        paragraphs.insert(1, seed_words)
    
    content = "\n\n".join(paragraphs)
    
    title_templates = [
        f"《{random.choice(['那年夏天', '那个教室', '青春', '毕业那天', '校服'])}》",
        f"《{random.choice(['回不去的', '后来的我们', '那些年'])}》",
    ]
    title = random.choice(title_templates)
    
    return {"title": title, "content": content, "style_id": "youth_campus", "style_label": "青春校园"}


def _gen_regret_lit(seed_words="", length="short"):
    """遗憾文学生成器：错过、来不及、如果当初"""
    images = random.sample(_REGRET_IMAGES, min(3, len(_REGRET_IMAGES)))
    phrases = random.sample(_REGRET_PHRASES, min(3, len(_REGRET_PHRASES)))
    
    paragraphs = []
    
    # 场景
    paragraphs.append(images[0] + "。")
    
    # 情绪
    paragraphs.append(phrases[0])
    
    # 深化
    paragraphs.append(images[1] + "。\n" + phrases[1])
    
    # 结尾留白
    paragraphs.append(phrases[2])
    
    if seed_words:
        paragraphs.insert(1, seed_words)
    
    content = "\n\n".join(paragraphs)
    
    title_templates = [
        f"《{random.choice(['遗憾', '如果', '后来', '错过', '来不及'])}》",
        f"《{random.choice(['差一点', '假如', '可惜', '再见了'])}》",
    ]
    title = random.choice(title_templates)
    
    return {"title": title, "content": content, "style_id": "regret_lit", "style_label": "遗憾文学"}


def _gen_healing_lit(seed_words="", length="short"):
    """治愈文学生成器：温柔、希望、与自己和解"""
    images = random.sample(_HEALING_IMAGES, min(3, len(_HEALING_IMAGES)))
    phrases = random.sample(_HEALING_PHRASES, min(3, len(_HEALING_PHRASES)))
    
    paragraphs = []
    
    # 温暖场景
    paragraphs.append(images[0] + "。")
    
    # 治愈话语
    paragraphs.append(phrases[0])
    
    # 场景 + 话语
    paragraphs.append(images[1] + "。\n" + phrases[1])
    
    # 结尾希望
    paragraphs.append(phrases[2])
    
    if seed_words:
        paragraphs.insert(1, seed_words)
    
    content = "\n\n".join(paragraphs)
    
    title_templates = [
        f"《{random.choice(['没关系', '慢慢来', '会好的', '温柔', '晚安'])}》",
        f"《{random.choice(['给自己', '致自己', '明天', '一切都会好的'])}》",
    ]
    title = random.choice(title_templates)
    
    return {"title": title, "content": content, "style_id": "healing_lit", "style_label": "治愈文学"}


def _gen_late_night(seed_words="", length="short"):
    """深夜情绪生成器：凌晨、独处、克制表达"""
    images = random.sample(_LATE_NIGHT_IMAGES, min(3, len(_LATE_NIGHT_IMAGES)))
    phrases = random.sample(_LATE_NIGHT_PHRASES, min(3, len(_LATE_NIGHT_PHRASES)))
    
    paragraphs = []
    
    # 深夜场景
    paragraphs.append(images[0] + "。")
    
    # 情绪
    paragraphs.append(phrases[0])
    
    # 深化
    paragraphs.append(images[1] + "。\n" + phrases[1])
    
    # 结尾
    paragraphs.append(phrases[2])
    
    if seed_words:
        paragraphs.insert(1, seed_words)
    
    content = "\n\n".join(paragraphs)
    
    title_templates = [
        f"《{random.choice(['凌晨', '深夜', '失眠', '晚安', '零点'])}》",
        f"《{random.choice(['睡不着', '夜', '一个人的夜', '凌晨三点'])}》",
    ]
    title = random.choice(title_templates)
    
    return {"title": title, "content": content, "style_id": "late_night", "style_label": "深夜情绪"}


def _gen_short_sentence(seed_words="", length="short"):
    """高级短句生成器：字数极少、密度极高"""
    sentences = random.sample(_SHORT_SENTENCES, min(5, len(_SHORT_SENTENCES)))
    
    if seed_words:
        content = seed_words + "\n\n" + "\n\n".join(sentences[:4])
    else:
        content = "\n\n".join(sentences)
    
    title = f"《{random.choice(['短句', '一句话', '瞬间', '心情', '碎片'])}》"
    
    return {"title": title, "content": content, "style_id": "short_sentence", "style_label": "高级短句"}


def _gen_viral_essay(seed_words="", length="short"):
    """网感文学生成器：口语化、有共鸣、有网感"""
    topics = random.sample(_VIRAL_TOPICS, min(2, len(_VIRAL_TOPICS)))
    endings = random.sample(_VIRAL_ENDINGS, min(2, len(_VIRAL_ENDINGS)))
    
    paragraphs = []
    
    # 开头：引起共鸣
    paragraphs.append(topics[0] + "。")
    
    # 中间：展开叙述
    if seed_words:
        paragraphs.append(seed_words)
    
    # 情绪递进
    paragraphs.append(topics[1] + "。")
    
    # 结尾：互动式收束
    paragraphs.append(endings[0])
    
    content = "\n\n".join(paragraphs)
    
    title_templates = [
        f"《{random.choice(['你有没有', '后来我才明白', '其实我们都知道', '今天突然发现'])}》",
        f"《{random.choice(['成年人的', '关于', '写给', '深夜有感'])}》",
    ]
    title = random.choice(title_templates)
    
    return {"title": title, "content": content, "style_id": "viral_essay", "style_label": "网感文学"}


# ============================
# 风格生成器注册表
# ============================

STYLE_GENERATORS = {
    "modern_poetry": _gen_modern_poetry,
    "white_space": _gen_white_space,
    "youth_campus": _gen_youth_campus,
    "regret_lit": _gen_regret_lit,
    "healing_lit": _gen_healing_lit,
    "late_night": _gen_late_night,
    "short_sentence": _gen_short_sentence,
    "viral_essay": _gen_viral_essay,
}


def generate_with_style(style_id=None, seed_words="", length="short", auto_mix=True):
    """
    按风格生成短文（v2 升级版）
    
    参数:
        style_id: 指定风格 ID，None 则使用 auto_mix
        seed_words: 用户输入的关键词/主题
        length: short / medium / long
        auto_mix: 是否启用自动混合模式（默认 True）
    
    返回:
        {"title": str, "content": str, "style_id": str, "style_label": str}
    """
    if auto_mix or not style_id:
        # 按权重随机选择风格
        weights = AUTO_MIX_CONFIG["weights"]
        active = [(s, w) for s, w in weights.items() if w > 0]
        if not active:
            style_id = "modern_poetry"
        else:
            styles, weights_list = zip(*active)
            style_id = random.choices(styles, weights=weights_list, k=1)[0]
    
    generator = STYLE_GENERATORS.get(style_id)
    if not generator:
        style_id = "modern_poetry"
        generator = STYLE_GENERATORS[style_id]
    
    result = generator(seed_words=seed_words, length=length)
    
    # 根据 length 参数截取内容
    target_len = {"short": 200, "medium": 350, "long": 500}.get(length, 200)
    if len(result["content"]) > target_len:
        lines = result["content"].split("\n\n")
        truncated = []
        total = 0
        for line in lines:
            if total + len(line) > target_len:
                break
            truncated.append(line)
            total += len(line)
        if len(truncated) < len(lines) and truncated:
            truncated.append(lines[-1])  # 保留结尾
        result["content"] = "\n\n".join(truncated) if truncated else result["content"]
    
    return result
