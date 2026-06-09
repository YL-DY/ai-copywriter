# -*- coding: utf-8 -*-
"""在 app.py 中插入 /api/today-sentence 相关路由"""
import re

path = "d:/projects/ai-copywriter/app.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 要插入的 3 个路由代码
new_routes = r'''

@app.route("/api/today-sentence")
def api_today_sentence():
    """从数据库随机抽取一条作品作为今日句子"""
    import random as _random
    history = History.query.filter(
        History.result.isnot(None),
        History.result != ''
    ).order_by(db.func.random()).first()
    if history and history.result and history.result.strip():
        text = history.result.strip()
        author = history.user.nickname or history.user.username if history.user else "匿名用户"
        style = map_style_name(history.style) if history.style else ""
        source = f"\u2014\u2014 {author} \u00b7 {style}" if style else f"\u2014\u2014 {author}"
        return jsonify({"ok": True, "text": text, "author": author, "style": style, "source": source, "history_id": history.id, "from_db": True})
    fallback = _random.choice(TODAY_SENTENCES)
    return jsonify({"ok": True, "text": fallback, "author": "InkFlow", "style": "", "source": "\u2014\u2014 InkFlow \u00b7 \u6bcf\u65e5\u4e00\u53e5", "history_id": None, "from_db": False})


@app.route("/api/today-sentence/fav", methods=["POST"])
@login_required
def api_today_sentence_fav():
    """收藏/取消收藏今日句子"""
    data = request.get_json() or {}
    text = data.get("text", "")
    author = data.get("author", "")
    style = data.get("style", "")
    history_id = data.get("history_id")
    if not text:
        return jsonify({"ok": False, "error": "\u7f3a\u5c11\u6587\u672c"}), 200
    import hashlib as _hashlib
    pick_id = "sentence_" + _hashlib.md5(text.encode()).hexdigest()[:12]
    existing = Favorite.query.filter_by(user_id=current_user.id, pick_id=pick_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"ok": True, "faved": False})
    pick_data = {"title": "\u4eca\u65e5\u53e5\u5b50\u6458\u5f55", "content": text, "author": author, "style": style, "world_label": style or "\u6587\u5b66", "history_id": history_id}
    import json as _json
    fav = Favorite(user_id=current_user.id, pick_id=pick_id, pick_data=_json.dumps(pick_data, ensure_ascii=False))
    db.session.add(fav)
    db.session.commit()
    return jsonify({"ok": True, "faved": True})


@app.route("/api/today-sentence/hot")
def api_today_sentence_hot():
    """获取热门摘录排行（基于收藏次数）"""
    import json as _json
    from sqlalchemy import func as _func
    hot_favs = db.session.query(Favorite.pick_id, _func.count(Favorite.id).label('fav_count')).filter(
        Favorite.pick_id.isnot(None),
        Favorite.pick_id.like('sentence_%')
    ).group_by(Favorite.pick_id).order_by(_func.count(Favorite.id).desc()).limit(10).all()
    items = []
    seen = set()
    for pick_id, count in hot_favs:
        if pick_id in seen:
            continue
        seen.add(pick_id)
        fav_sample = Favorite.query.filter_by(pick_id=pick_id).first()
        if fav_sample and fav_sample.pick_data:
            try:
                data = _json.loads(fav_sample.pick_data)
                items.append({
                    "pick_id": pick_id,
                    "text": data.get("content", "")[:100],
                    "author": data.get("author", ""),
                    "style": data.get("style", ""),
                    "fav_count": count
                })
            except Exception:
                pass
    return jsonify({"ok": True, "items": items})

'''

# 在 @app.route("/api/daily/picks") 之前插入
marker = '\n@app.route("/api/daily/picks")'
insert_pos = content.find(marker)

if insert_pos == -1:
    print("ERROR: Could not find marker '@app.route(\"/api/daily/picks\")'")
    exit(1)

new_content = content[:insert_pos] + new_routes + content[insert_pos:]

with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)

# 验证
count = new_content.count("/api/today-sentence")
print(f"Routes inserted successfully! Found {count} occurrences of '/api/today-sentence'")
