"""
香疯了 - 正常度打分服务（规则层 + 朴素贝叶斯 v2）
==================================================
"""

import jieba
import joblib


# ============================================================
# 经典异常菜白名单
# ============================================================

CLASSIC_UNUSUAL = {
    frozenset(["菠萝", "猪肉"]): 80,
    frozenset(["菠萝", "排骨"]): 80,
    frozenset(["菠萝", "鸡胸肉"]): 75,
    frozenset(["芒果", "鸡胸肉"]): 75,
    frozenset(["芒果", "虾"]): 75,
    frozenset(["芒果", "虾仁"]): 75,
    frozenset(["柠檬", "鸡腿"]): 75,
    frozenset(["柠檬", "鸡翅"]): 75,
    frozenset(["柠檬", "鱼"]): 80,
    frozenset(["柠檬", "鲈鱼"]): 80,
    frozenset(["柠檬", "虾"]): 80,
    frozenset(["柠檬", "虾仁"]): 80,
    frozenset(["百香果", "排骨"]): 75,
    frozenset(["山楂", "排骨"]): 80,
    frozenset(["山楂", "猪蹄"]): 75,
    frozenset(["橙子", "鸭肉"]): 75,
    frozenset(["苹果", "排骨"]): 70,
    frozenset(["木瓜", "排骨"]): 80,
    frozenset(["椰子", "鸡肉"]): 80,
    frozenset(["啤酒", "鸭肉"]): 85,
    frozenset(["啤酒", "鸭"]): 85,
    frozenset(["啤酒", "鱼"]): 75,
    frozenset(["可乐", "鸡翅"]): 85,
    frozenset(["可乐", "排骨"]): 80,
    frozenset(["可乐", "鸡翅中"]): 85,
    frozenset(["咖啡", "排骨"]): 70,
    frozenset(["红酒", "牛肉"]): 85,
    frozenset(["红酒", "牛腩"]): 85,
    frozenset(["黄酒", "鸡"]): 80,
    frozenset(["米酒", "鸡"]): 80,
}

# ============================================================
# 食材类别词典
# ============================================================

CATEGORY = {
    "甜品甜食": {
        "冰淇淋", "巧克力", "奶油", "蛋糕", "饼干", "果酱", "蜂蜜", "炼乳",
        "布丁", "泡芙", "慕斯", "太妃糖", "棉花糖", "棒棒糖", "果冻",
        "奶昔", "蜜饯", "椰果", "抹茶粉", "可可粉", "糖浆", "枫糖浆",
        "红豆沙", "奥利奥", "威化", "马卡龙", "珍珠奶茶",
    },
    "内脏下水": {
        "腰花", "猪肝", "猪心", "肥肠", "猪大肠", "牛肚", "毛肚",
        "鸡胗", "鸡肫", "鸭胗", "鸭肠", "鹅肝", "猪腰", "牛百叶",
        "鸡心", "鸭血", "猪血", "牛鞭", "牛尾", "猪尾巴", "鸡屁股",
        "鸡脖", "鸭掌", "鸡爪", "猪蹄", "猪耳朵", "鸭舌", "兔头",
        "毛血旺", "猪脑", "羊杂",
    },
    "水果": {
        "西瓜", "草莓", "芒果", "香蕉", "葡萄", "柠檬", "橙子",
        "苹果", "梨", "桃子", "火龙果", "荔枝", "山竹", "哈密瓜",
        "西柚", "榴莲", "蓝莓", "樱桃", "猕猴桃", "木瓜", "百香果",
        "椰子", "杨梅", "石榴", "柿子", "菠萝", "山楂",
    },
    "重口调料": {
        "豆瓣酱", "老干妈", "剁椒", "豆豉", "腐乳", "臭豆腐",
        "鱼露", "虾酱", "螺蛳酱", "麻辣酱", "辣根", "芥末", "黄芥末",
    },
    "饮料零食": {
        "可乐", "雪碧", "啤酒", "薯片", "爆米花", "辣条",
        "方便面", "话梅", "瓜子",
    },
}

CONFLICT_RULES = [
    ("甜品甜食", "内脏下水", "hard"),
    ("甜品甜食", "重口调料", "hard"),
    ("水果", "内脏下水", "soft"),
    ("水果", "重口调料", "soft"),
    ("饮料零食", "内脏下水", "soft"),
]

COMMON_INGREDIENTS = {
    "番茄", "西红柿", "土豆", "青椒", "黄瓜", "茄子", "豆角", "白菜",
    "大白菜", "小白菜", "菠菜", "生菜", "油菜", "青菜", "芹菜", "韭菜",
    "莴笋", "西兰花", "花菜", "菜花", "胡萝卜", "萝卜", "白萝卜", "山药",
    "南瓜", "冬瓜", "丝瓜", "苦瓜", "洋葱", "蘑菇", "香菇", "平菇",
    "金针菇", "木耳", "银耳", "豆芽", "藕", "莲藕", "玉米", "毛豆",
    "秋葵", "芦笋", "竹笋", "荷兰豆",
    "猪肉", "五花肉", "猪里脊", "猪里脊肉", "排骨", "肋排", "肉末",
    "肉丝", "肉片", "牛肉", "牛腩", "牛肉片", "鸡肉", "鸡胸肉",
    "鸡腿", "鸡翅", "鸡翅中", "鸭肉", "羊肉", "羊腿", "猪肉末",
    "虾", "虾仁", "鱼", "鲈鱼", "带鱼", "三文鱼", "鱿鱼", "螃蟹",
    "蛤蜊", "花蛤", "扇贝",
    "鸡蛋", "鸭蛋", "皮蛋", "豆腐", "嫩豆腐", "老豆腐", "豆腐皮",
    "腐竹", "豆干", "牛奶",
    "米饭", "面条", "挂面", "面粉", "米粉", "粉丝", "年糕", "饺子皮",
    "馄饨皮", "剩米饭",
    "花生", "腊肉", "腊肠", "火腿", "火腿肠", "培根", "午餐肉",
    "虾皮", "紫菜", "海带", "粉条",
    "盐", "糖", "白糖", "冰糖", "红糖", "生抽", "老抽", "醋", "陈醋",
    "香醋", "料酒", "蚝油", "味精", "鸡精", "胡椒粉", "白胡椒",
    "花椒", "花椒粉", "八角", "桂皮", "香叶", "干辣椒", "辣椒粉",
    "五香粉", "十三香", "淀粉", "番茄酱", "芝麻油", "香油",
    "油", "色拉油", "橄榄油", "黄油",
    "酱油", "食用油", "菜籽油", "花生油", "猪油",
    "水淀粉", "玉米淀粉", "红薯淀粉",
    "白醋", "米醋", "黑醋", "黄酒", "白酒",
    "豆瓣酱", "郫县豆瓣酱", "甜面酱", "芝麻酱",
    "孜然", "孜然粉", "咖喱粉", "咖喱",
    "葱", "小葱", "葱花", "大葱", "葱段", "葱白",
    "姜", "生姜", "姜片", "姜丝", "姜末",
    "蒜", "大蒜", "蒜末", "蒜蓉", "蒜片", "蒜瓣",
    "香菜", "小米辣",
}


# ============================================================
# 规则层
# ============================================================

def _check_classic_unusual(ingredients, seasonings=None):
    all_items = set(ingredients + (seasonings or []))
    best = None
    for combo, floor_score in CLASSIC_UNUSUAL.items():
        if combo.issubset(all_items):
            if best is None or floor_score > best:
                best = floor_score
    return best


def _categorize(ingredients):
    result = {}
    for ing in ingredients:
        for cat_name, cat_words in CATEGORY.items():
            if ing in cat_words:
                result.setdefault(cat_name, set()).add(ing)
    return result


def _check_conflicts(categorized):
    triggered = []
    for cat_a, cat_b, severity in CONFLICT_RULES:
        if cat_a in categorized and cat_b in categorized:
            triggered.append({
                "categories": (cat_a, cat_b),
                "items_a": list(categorized[cat_a]),
                "items_b": list(categorized[cat_b]),
                "severity": severity,
            })
    return triggered


def rule_layer(ingredients, seasonings=None):
    all_items = ingredients + (seasonings or [])
    classic_floor = _check_classic_unusual(ingredients, seasonings)
    categorized = _categorize(all_items)
    conflicts = _check_conflicts(categorized)

    known = sum(1 for i in all_items if i in COMMON_INGREDIENTS)
    whitelist_ratio = known / len(all_items) if all_items else 0.0

    adjustment = 0.0
    floor = None
    boost = 0.0
    reasons = []

    if classic_floor is not None:
        reasons.append(f"命中经典菜白名单，保底 {classic_floor} 分")
    else:
        for c in conflicts:
            if c["severity"] == "hard":
                floor = 30.0
                adjustment -= 40
                reasons.append(f"{c['categories'][0]}×{c['categories'][1]}=极其离谱")
            elif c["severity"] == "soft":
                adjustment -= 25
                reasons.append(f"{c['categories'][0]}×{c['categories'][1]}=比较离谱")

    if whitelist_ratio == 1.0 and not conflicts:
        boost = 10.0
    elif whitelist_ratio >= 0.8 and not conflicts:
        boost = 5.0

    return {
        "adjustment": adjustment,
        "floor": floor,
        "classic_floor": classic_floor,
        "boost": boost,
        "conflicts": conflicts,
        "whitelist_ratio": whitelist_ratio,
        "reasons": reasons,
    }


# ============================================================
# 主打分类
# ============================================================

class NormalityScorer:
    def __init__(self):
        self.clf = None
        self.vectorizer = None

    def load(self, clf_path: str, vec_path: str):
        self.clf = joblib.load(clf_path)
        self.vectorizer = joblib.load(vec_path)
        print("✅ 正常度打分模型加载完成")

    def _bayes_score(self, text: str) -> float:
        tokenized = " ".join(jieba.cut(text))
        vec = self.vectorizer.transform([tokenized])
        proba = self.clf.predict_proba(vec)[0]
        return float(proba[1]) * 100

    def score_recipe(self, ingredients, seasonings=None, verbose=False):
        all_items = ingredients + (seasonings or [])
        text = " ".join(all_items)

        bayes_raw = self._bayes_score(text)
        rules = rule_layer(ingredients, seasonings)

        if rules["classic_floor"] is not None:
            final = max(bayes_raw, rules["classic_floor"]) + rules["boost"]
        else:
            final = bayes_raw + rules["adjustment"] + rules["boost"]
            if rules["floor"] is not None:
                final = min(final, rules["floor"])
            if rules["whitelist_ratio"] == 1.0 and not rules["conflicts"]:
                final = max(final, 55.0)

        final = max(0.0, min(100.0, round(final, 1)))

        if final >= 70:
            label = "正常"
        elif final >= 40:
            label = "冒险"
        else:
            label = "勇士"

        result = {
            "normality_score": final,
            "label": label,
            "bayes_raw": round(bayes_raw, 1),
        }
        if verbose:
            result["reasons"] = rules["reasons"]

        return result
