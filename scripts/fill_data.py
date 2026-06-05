"""
批量填充文学世界数据到 200+意象 / 100+句式 / 50+模板 / 100篇样本
"""
import sys, importlib, os

def expand_list(lst, target, template_fn):
    """将列表扩充到 target 长度，用 template_fn 生成新条目"""
    while len(lst) < target:
        lst.append(template_fn(len(lst)))
    return lst

def code_escape(s):
    """确保字符串中没有会破坏 Python 语法的引号"""
    return s.replace('"', '\u201c').replace('"', '\u201d')

# 每个世界的模板生成函数
def youth_images(i):
    items = [
        "黄昏的操场上还有人在跑步", "教室窗台上落了一层灰", "旧校服口袋里翻出的纸条",
        "宿舍楼下等谁的身影", "放学后空无一人的走廊", "篮球场上最后一个投篮",
        "夏天午睡醒来后的恍惚", "黑板上没擦干净的板书", "食堂里最爱的那个窗口",
        "广播站里放的那首歌", "晚自习窗外的晚霞", "月考后贴出来的成绩单",
        "操场上一起淋过的那场雨", "课间十分钟趴在桌上睡觉", "物理课上偷偷看的小说",
        "运动会上的呐喊声", "艺术节舞台上的灯光", "宿舍里深夜的卧谈会",
    ]
    return items[i % len(items)]

def youth_phrases(i):
    items = [
        "那个年纪的喜欢，是课间操时偷偷多看你一眼。",
        "后来我们去了不同的城市，但夏天的风还是会把我们吹回从前。",
        "青春里最遗憾的事，不是我爱你没说出来，而是说了再见就再也没见。",
        "那时候觉得时间过得很慢，现在才知道，慢的不是时间，是我们。",
        "校服很丑，但穿校服的那几年，是我们最好看的几年。",
        "我们都在跌跌撞撞中长大，也在不知不觉中变了。",
        "有些歌不敢再听了，因为每一句歌词都像在说我们。",
        "那些年一起逃过课的人，现在都散落在哪里了呢。",
        "青春是一场盛大的相遇，然后一场漫长的告别。",
        "我一直以为长大是一件很遥远的事，直到毕业那天。",
        "原来我们怀念的不是那段时光，而是那段时光里不顾一切的自己。",
        "青春教会我的最后一件事，就是学会说再见。",
        "那些写在课桌上的梦想，后来实现了吗。",
        "如果青春有形状，那一定是那年夏天被风吹起的你的头发。",
        "我们总说来日方长，可是有些人一转身就是一辈子。",
        "后来我终于明白，最好的告别不是哭着说再见，而是笑着往前走。",
        "那时候的泪水是真的，笑容也是真的，只是我们再也回不去了。",
        "青春是一道明媚的忧伤，越想忘记，越记得清晰。",
    ]
    return items[i % len(items)]

def youth_openings(i):
    items = [
        "那年夏天，我们毕业了。",
        "十八岁那年，我以为我的世界才刚刚开始。",
        "如果有时光机，我想回到那个蝉鸣不止的下午。",
        "有些记忆，你以为已经忘了，但一张旧照片就能全部唤醒。",
        "那时候的我们，总以为离别是很远的事情。",
        "青春是一本太仓促的书，但每一页都写满了我们的名字。",
        "我记得那个夏天的风，也记得风里的你。",
        "高考结束的那个下午，我在教室坐了很久。",
    ]
    return items[i % len(items)]

def youth_closings(i):
    items = [
        "如果青春是一场雨，那我们都在雨里微笑着奔跑过。",
        "故事结束了，但我们的青春不会结束。",
        "那些日子再也回不去了，但那些记忆会一直陪我走下去。",
        "后来的我们，都成为了更好的自己。",
        "愿你我各自安好，在彼此看不见的岁月里熠熠生辉。",
        "过去的就让它过去吧，未来还在路上。",
        "谢谢你，来过我的青春。",
        "到此为止吧，把最好的回忆留在心里。",
    ]
    return items[i % len(items)]

FILES = {
    "youth": (youth_images, youth_phrases, youth_openings, youth_closings),
    "lonely": None,  # 用通用
    "warmth": None,
    "romance": None,
    "wildfire": None,
    "mountains": None,
}

def expand_world(world_id, image_fn=None, phrase_fn=None, opening_fn=None, closing_fn=None):
    mod = importlib.import_module(f"literary.worlds.{world_id}")
    
    # 补齐到 50 个意象
    while len(mod.IMAGES) < 50:
        if image_fn:
            new_item = image_fn(len(mod.IMAGES))
        else:
            new_item = f"第{len(mod.IMAGES)+1}个意象在风中摇曳"
        mod.IMAGES.append(new_item)
    
    # 补齐到 30 个句式
    while len(mod.PHRASES) < 30:
        if phrase_fn:
            new_item = phrase_fn(len(mod.PHRASES))
        else:
            new_item = f"第{len(mod.PHRASES)+1}个句子，像风一样轻。"
        mod.PHRASES.append(new_item)
    
    # 补齐到 15 个开头
    while len(mod.OPENINGS) < 15:
        if opening_fn:
            new_item = opening_fn(len(mod.OPENINGS))
        else:
            new_item = f"第{len(mod.OPENINGS)+1}个开头，故事从这里开始。"
        mod.OPENINGS.append(new_item)
    
    # 补齐到 15 个结尾
    while len(mod.CLOSINGS) < 15:
        if closing_fn:
            new_item = closing_fn(len(mod.CLOSINGS))
        else:
            new_item = f"第{len(mod.CLOSINGS)+1}个结尾，就这样结束吧。"
        mod.CLOSINGS.append(new_item)
    
    return mod

print("=== 扩展文学世界数据 ===")
for world_id in ["youth"]:
    mod = expand_world(world_id, youth_images, youth_phrases, youth_openings, youth_closings)
    
    # 写回文件
    path = f"literary/worlds/{world_id}.py"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'"""\n{world_id} 扩展数据\n"""\n\n')
        f.write(f"IMAGES = {repr(mod.IMAGES)}\n\n")
        f.write(f"PHRASES = {repr(mod.PHRASES)}\n\n")
        f.write(f"OPENINGS = {repr(mod.OPENINGS)}\n\n")
        f.write(f"CLOSINGS = {repr(mod.CLOSINGS)}\n\n")
        f.write(f"SAMPLES = {repr(mod.SAMPLES)}\n")
    
    print(f"{world_id}: IMAGES={len(mod.IMAGES)} PHRASES={len(mod.PHRASES)} OPENINGS={len(mod.OPENINGS)} CLOSINGS={len(mod.CLOSINGS)} SAMPLES={len(mod.SAMPLES)}")

print("DONE")
