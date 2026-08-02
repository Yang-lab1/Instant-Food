"""
菜品正常度评分服务
=================
放置路径: backend/services/normality_service.py
依赖文件: backend/models/best_model.pkl
          backend/models/cooccur_freq.pkl

需要的依赖 (加到 requirements.txt):
    scikit-learn
    xgboost
    numpy
    pandas
"""

import logging
import pickle
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from config import settings

logger = logging.getLogger(__name__)

# ── 模型文件路径（相对于项目根目录）──
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
MODEL_PATH = BASE_DIR / "models" / "best_model.pkl"
COOCCUR_PATH = BASE_DIR / "models" / "cooccur_freq.pkl"

# ── 食材归一化 ──
SYNONYM_MAP = {
    "西红柿": "番茄", "圣女果": "小番茄",
    "土豆": "马铃薯", "洋芋": "马铃薯",
    "鸡蛋": "蛋", "蛋黄": "蛋", "蛋清": "蛋",
    "大蒜": "蒜", "蒜头": "蒜", "蒜瓣": "蒜", "蒜末": "蒜",
    "大葱": "葱", "小葱": "葱", "葱花": "葱", "香葱": "葱",
    "老姜": "姜", "生姜": "姜", "姜片": "姜",
    "五花肉": "猪肉", "里脊肉": "猪肉", "排骨": "猪肉", "瘦肉": "猪肉",
    "鸡胸肉": "鸡肉", "鸡腿肉": "鸡肉", "鸡翅": "鸡肉",
    "牛腩": "牛肉", "肥牛": "牛肉",
    "生抽": "酱油", "老抽": "酱油",
    "花生油": "食用油", "菜籽油": "食用油", "橄榄油": "食用油", "植物油": "食用油", "油": "食用油",
    "白砂糖": "糖", "冰糖": "糖", "红糖": "糖", "白糖": "糖",
    "食盐": "盐",
    "陈醋": "醋", "米醋": "醋", "白醋": "醋",
}

CONDIMENTS = {
    "盐", "糖", "酱油", "醋", "料酒", "食用油", "蚝油", "味精", "鸡精",
    "胡椒粉", "花椒", "八角", "桂皮", "香叶", "豆瓣酱", "番茄酱",
    "芝麻油", "麻油", "淀粉", "生粉", "面粉", "五香粉", "十三香",
    "孜然", "咖喱粉", "辣椒粉", "豆豉", "腐乳", "甜面酱", "黄豆酱",
    "蒜", "葱", "姜", "干辣椒", "辣椒", "芝麻", "白芝麻",
    "水", "清水", "温水", "热水",
}


class NormalityScorer:
    """
    菜品正常度评分器

    调用方式:
        scorer = NormalityScorer()
        result = scorer.score(
            ingredients=["番茄", "巧克力", "鸡蛋"],
            cooking_method="炒"
        )
        # result = {
        #     "normality_score": 19.3,
        #     "verdict": "这真的能吃吗？！",
        #     "level": "crazy",
        #     "main_ingredients": ["番茄", "巧克力", "蛋"],
        #     "condiments": [],
        #     "cooking_method": "炒"
        # }
    """

    def __init__(self):
        self.model = None
        self.feature_names = []
        self.cooccur_freq = {}
        self._load_attempted = False
        self._available = False

    @property
    def available(self) -> bool:
        if not self._load_attempted:
            self._load()
        return self._available

    def _load(self) -> None:
        self._load_attempted = True

        if not settings.enable_traditional_normality:
            logger.info("Traditional normality scoring is disabled by config.")
            return

        if not MODEL_PATH.exists() or not COOCCUR_PATH.exists():
            logger.warning(
                "Traditional normality model files are missing: model=%s cooccur=%s",
                MODEL_PATH,
                COOCCUR_PATH,
            )
            return

        try:
            with open(MODEL_PATH, "rb") as f:
                artifact = pickle.load(f)
            with open(COOCCUR_PATH, "rb") as f:
                self.cooccur_freq = pickle.load(f)

            self.model = artifact["model"]
            self.feature_names = artifact["feature_names"]
            self._available = True
            logger.info("Traditional normality scorer loaded successfully.")
        except Exception as error:  # pragma: no cover - runtime model loading
            logger.warning("Failed to load traditional normality scorer: %s", error)
            self._available = False

    def _normalize(self, name: str) -> str:
        return SYNONYM_MAP.get(name.strip(), name.strip())

    def _classify(self, name: str) -> str:
        return "condiment" if name in CONDIMENTS else "main"

    def _split_ingredients(self, ingredients: list[str]) -> tuple[list[str], list[str]]:
        """自动把用户输入的食材列表拆分成主料和调料"""
        mains, conds = [], []
        for ing in ingredients:
            normalized = self._normalize(ing)
            if not normalized:
                continue
            if self._classify(normalized) == "condiment":
                if normalized not in conds:
                    conds.append(normalized)
            else:
                if normalized not in mains:
                    mains.append(normalized)
        return mains, conds

    def _compute_cooccurrence(self, mains: list, conds: list) -> dict:
        all_items = list(set(mains + conds))
        pairs = list(combinations(sorted(all_items), 2))

        if not pairs:
            return {
                "avg_cooccur": 0.0, "min_cooccur": 0.0, "max_cooccur": 0.0,
                "zero_pair_ratio": 1.0, "avg_main_cooccur": 0.0, "avg_cross_cooccur": 0.0,
            }

        freqs = [self.cooccur_freq.get(p, 0.0) for p in pairs]
        zero_count = sum(1 for f in freqs if f == 0)

        main_set, cond_set = set(mains), set(conds)
        main_pairs = [(a, b) for a, b in pairs if a in main_set and b in main_set]
        main_freqs = [self.cooccur_freq.get(p, 0.0) for p in main_pairs] if main_pairs else [0.0]
        cross_pairs = [(a, b) for a, b in pairs
                       if (a in main_set and b in cond_set) or (a in cond_set and b in main_set)]
        cross_freqs = [self.cooccur_freq.get(p, 0.0) for p in cross_pairs] if cross_pairs else [0.0]

        return {
            "avg_cooccur": float(np.mean(freqs)),
            "min_cooccur": float(np.min(freqs)),
            "max_cooccur": float(np.max(freqs)),
            "zero_pair_ratio": zero_count / len(pairs),
            "avg_main_cooccur": float(np.mean(main_freqs)),
            "avg_cross_cooccur": float(np.mean(cross_freqs)),
        }

    def score(
        self,
        ingredients: list[str],
        cooking_method: str = "炒",
        seasonings: Optional[list[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        主接口：输入食材列表 + 烹饪方法，返回正常度评分

        Parameters:
            ingredients: 食材列表，不用区分主料/调料，会自动分类
                         例: ["番茄", "鸡蛋", "盐", "糖", "食用油"]
            cooking_method: 烹饪方法，可选值: 炒/煮/蒸/炖/烤/煎/炸/拌/烧/卤/煲/烙
                            默认"炒"

        Returns:
            {
                "normality_score": float,    # 0-100 正常度百分数
                "verdict": str,              # 中文判定语
                "level": str,                # normal/creative/adventurous/crazy/insane
                "main_ingredients": list,    # 归一化后的主料
                "condiments": list,          # 归一化后的调料
                "cooking_method": str
            }
        """
        if not self.available:
            return None

        all_items = [str(item or "").strip() for item in (ingredients + (seasonings or []))]
        all_items = [item for item in all_items if item]
        if not all_items:
            return None

        mains, conds = self._split_ingredients(all_items)

        cooccur_feats = self._compute_cooccurrence(mains, conds)

        feat = {}
        for fname in self.feature_names:
            if fname.startswith("ing_"):
                feat[fname] = 1 if fname[4:] in mains else 0
            elif fname.startswith("cond_"):
                feat[fname] = 1 if fname[5:] in conds else 0
            elif fname.startswith("cook_"):
                feat[fname] = 1 if fname[5:] == cooking_method else 0
            elif fname == "n_ingredients":
                feat[fname] = len(mains)
            elif fname == "n_condiments":
                feat[fname] = len(conds)
            elif fname in cooccur_feats:
                feat[fname] = cooccur_feats[fname]
            else:
                feat[fname] = 0

        X = np.array([[feat[name] for name in self.feature_names]], dtype=float)

        prob = float(self.model.predict_proba(X)[0, 1])
        score = round(prob * 100, 1)

        if score > 80:
            verdict, level, label, mood = "很正常的搭配", "normal", "正常", "稳了"
        elif score > 60:
            verdict, level, label, mood = "基本正常，有点小创意", "creative", "创意", "有点新意"
        elif score > 40:
            verdict, level, label, mood = "有点意思...算是冒险了", "adventurous", "冒险", "敢试"
        elif score > 20:
            verdict, level, label, mood = "相当疯狂，但也许有惊喜？", "crazy", "疯狂", "上头"
        else:
            verdict, level, label, mood = "这真的能吃吗？！", "insane", "黑暗", "别试"

        return {
            "normality_score": score,
            "verdict": verdict,
            "level": level,
            "label": label,
            "mood": mood,
            "text": f"{verdict}，正常度：{score:g}%",
            "main_ingredients": mains,
            "condiments": conds,
            "cooking_method": cooking_method,
        }


# ── 单例（后端启动时只加载一次模型）──
_scorer = None

def get_scorer() -> NormalityScorer:
    global _scorer
    if _scorer is None:
        _scorer = NormalityScorer()
    return _scorer


NormalityService = NormalityScorer


def get_normality_service() -> NormalityScorer:
    return get_scorer()
