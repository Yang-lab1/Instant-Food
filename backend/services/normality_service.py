"""Traditional normality scoring service backed by PKL artifacts."""

from __future__ import annotations

import logging
import pickle
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from config import settings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / settings.normality_model_path
COOCCUR_PATH = BASE_DIR / settings.normality_cooccur_path

SYNONYM_MAP = {
    "\u897f\u7ea2\u67ff": "\u756a\u8304",
    "\u5723\u5973\u679c": "\u5c0f\u756a\u8304",
    "\u571f\u8c46": "\u9a6c\u94c3\u85af",
    "\u6d0b\u828b": "\u9a6c\u94c3\u85af",
    "\u9e21\u86cb": "\u86cb",
    "\u86cb\u9ec4": "\u86cb",
    "\u86cb\u6e05": "\u86cb",
    "\u5927\u849c": "\u849c",
    "\u849c\u5934": "\u849c",
    "\u849c\u74e3": "\u849c",
    "\u849c\u672b": "\u849c",
    "\u5927\u8471": "\u8471",
    "\u5c0f\u8471": "\u8471",
    "\u8471\u82b1": "\u8471",
    "\u9999\u8471": "\u8471",
    "\u8001\u59dc": "\u59dc",
    "\u751f\u59dc": "\u59dc",
    "\u59dc\u7247": "\u59dc",
    "\u4e94\u82b1\u8089": "\u732a\u8089",
    "\u91cc\u810a\u8089": "\u732a\u8089",
    "\u6392\u9aa8": "\u732a\u8089",
    "\u7626\u8089": "\u732a\u8089",
    "\u9e21\u80f8\u8089": "\u9e21\u8089",
    "\u9e21\u817f\u8089": "\u9e21\u8089",
    "\u9e21\u7fc5": "\u9e21\u8089",
    "\u725b\u8169": "\u725b\u8089",
    "\u80a5\u725b": "\u725b\u8089",
    "\u751f\u62bd": "\u9171\u6cb9",
    "\u8001\u62bd": "\u9171\u6cb9",
    "\u82b1\u751f\u6cb9": "\u98df\u7528\u6cb9",
    "\u83dc\u7c7d\u6cb9": "\u98df\u7528\u6cb9",
    "\u6a44\u6984\u6cb9": "\u98df\u7528\u6cb9",
    "\u690d\u7269\u6cb9": "\u98df\u7528\u6cb9",
    "\u6cb9": "\u98df\u7528\u6cb9",
    "\u767d\u7802\u7cd6": "\u7cd6",
    "\u51b0\u7cd6": "\u7cd6",
    "\u7ea2\u7cd6": "\u7cd6",
    "\u767d\u7cd6": "\u7cd6",
    "\u98df\u76d0": "\u76d0",
    "\u9648\u918b": "\u918b",
    "\u7c73\u918b": "\u918b",
    "\u767d\u918b": "\u918b",
}

CONDIMENTS = {
    "\u76d0",
    "\u7cd6",
    "\u9171\u6cb9",
    "\u918b",
    "\u6599\u9152",
    "\u98df\u7528\u6cb9",
    "\u869d\u6cb9",
    "\u5473\u7cbe",
    "\u9e21\u7cbe",
    "\u80e1\u6912\u7c89",
    "\u82b1\u6912",
    "\u516b\u89d2",
    "\u6842\u76ae",
    "\u9999\u53f6",
    "\u8c46\u74e3\u9171",
    "\u756a\u8304\u9171",
    "\u829d\u9ebb\u6cb9",
    "\u9ebb\u6cb9",
    "\u6dc0\u7c89",
    "\u751f\u7c89",
    "\u9762\u7c89",
    "\u4e94\u9999\u7c89",
    "\u5341\u4e09\u9999",
    "\u5b5c\u7136",
    "\u5496\u55b1\u7c89",
    "\u8fa3\u6912\u7c89",
    "\u8c46\u8c49",
    "\u8150\u4e73",
    "\u751c\u9762\u9171",
    "\u9ec4\u8c46\u9171",
    "\u849c",
    "\u8471",
    "\u59dc",
    "\u5e72\u8fa3\u6912",
    "\u8fa3\u6912",
    "\u829d\u9ebb",
    "\u767d\u829d\u9ebb",
    "\u6c34",
    "\u6e05\u6c34",
    "\u6e29\u6c34",
    "\u70ed\u6c34",
}


class NormalityScorer:
    """Load the shipped PKL model pair and score ingredient combinations."""

    def __init__(self) -> None:
        self.model = None
        self.feature_names: list[str] = []
        self.cooccur_freq: dict[tuple[str, str], float] = {}
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
            with MODEL_PATH.open("rb") as model_file:
                artifact = pickle.load(model_file)
            with COOCCUR_PATH.open("rb") as cooccur_file:
                self.cooccur_freq = pickle.load(cooccur_file)

            self.model = artifact["model"]
            self.feature_names = list(artifact["feature_names"])
            self._available = True
            logger.info("Traditional normality scorer loaded successfully.")
        except Exception as error:  # pragma: no cover - runtime model loading
            logger.warning("Failed to load traditional normality scorer: %s", error)
            self._available = False

    def _normalize(self, name: str) -> str:
        cleaned = str(name or "").strip()
        return SYNONYM_MAP.get(cleaned, cleaned)

    def _classify(self, name: str) -> str:
        return "condiment" if name in CONDIMENTS else "main"

    def _split_ingredients(self, ingredients: list[str]) -> tuple[list[str], list[str]]:
        mains: list[str] = []
        condiments: list[str] = []
        for ingredient in ingredients:
            normalized = self._normalize(ingredient)
            if not normalized:
                continue
            bucket = condiments if self._classify(normalized) == "condiment" else mains
            if normalized not in bucket:
                bucket.append(normalized)
        return mains, condiments

    def _lookup_pair(self, pair: tuple[str, str]) -> float:
        if pair in self.cooccur_freq:
            return float(self.cooccur_freq[pair])
        return float(self.cooccur_freq.get((pair[1], pair[0]), 0.0))

    def _compute_cooccurrence(self, mains: list[str], condiments: list[str]) -> dict[str, float]:
        all_items = sorted(set(mains + condiments))
        pairs = list(combinations(all_items, 2))

        if not pairs:
            return {
                "avg_cooccur": 0.0,
                "min_cooccur": 0.0,
                "max_cooccur": 0.0,
                "zero_pair_ratio": 1.0,
                "avg_main_cooccur": 0.0,
                "avg_cross_cooccur": 0.0,
            }

        freqs = [self._lookup_pair(pair) for pair in pairs]
        zero_count = sum(1 for value in freqs if value == 0)

        main_set = set(mains)
        condiment_set = set(condiments)
        main_pairs = [pair for pair in pairs if pair[0] in main_set and pair[1] in main_set]
        main_freqs = [self._lookup_pair(pair) for pair in main_pairs] if main_pairs else [0.0]
        cross_pairs = [
            pair
            for pair in pairs
            if (pair[0] in main_set and pair[1] in condiment_set)
            or (pair[0] in condiment_set and pair[1] in main_set)
        ]
        cross_freqs = [self._lookup_pair(pair) for pair in cross_pairs] if cross_pairs else [0.0]

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
        cooking_method: str = "\u7092",
        seasonings: Optional[list[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self.available:
            return None

        all_items = [str(item or "").strip() for item in (ingredients + (seasonings or []))]
        all_items = [item for item in all_items if item]
        if not all_items:
            return None

        mains, condiments = self._split_ingredients(all_items)
        cooccur_feats = self._compute_cooccurrence(mains, condiments)

        feature_map: dict[str, float] = {}
        for feature_name in self.feature_names:
            if feature_name.startswith("ing_"):
                feature_map[feature_name] = 1.0 if feature_name[4:] in mains else 0.0
            elif feature_name.startswith("cond_"):
                feature_map[feature_name] = 1.0 if feature_name[5:] in condiments else 0.0
            elif feature_name.startswith("cook_"):
                feature_map[feature_name] = 1.0 if feature_name[5:] == cooking_method else 0.0
            elif feature_name == "n_ingredients":
                feature_map[feature_name] = float(len(mains))
            elif feature_name == "n_condiments":
                feature_map[feature_name] = float(len(condiments))
            elif feature_name in cooccur_feats:
                feature_map[feature_name] = cooccur_feats[feature_name]
            else:
                feature_map[feature_name] = 0.0

        matrix = np.array([[feature_map[name] for name in self.feature_names]], dtype=float)
        probability = float(self.model.predict_proba(matrix)[0, 1])
        score = round(probability * 100.0, 1)

        if score > 80:
            verdict, level, label, mood = "\u5f88\u6b63\u5e38\u7684\u642d\u914d", "normal", "\u6b63\u5e38", "\u7a33\u4e86"
        elif score > 60:
            verdict, level, label, mood = "\u57fa\u672c\u6b63\u5e38\uff0c\u6709\u70b9\u5c0f\u521b\u610f", "creative", "\u521b\u610f", "\u6709\u70b9\u65b0\u610f"
        elif score > 40:
            verdict, level, label, mood = "\u6709\u70b9\u610f\u601d...\u7b97\u662f\u5192\u9669\u4e86", "adventurous", "\u5192\u9669", "\u6562\u8bd5"
        elif score > 20:
            verdict, level, label, mood = "\u76f8\u5f53\u75af\u72c2\uff0c\u4f46\u4e5f\u8bb8\u6709\u60ca\u559c\uff1f", "crazy", "\u75af\u72c2", "\u4e0a\u5934"
        else:
            verdict, level, label, mood = "\u8fd9\u771f\u7684\u80fd\u5403\u5417\uff1f\uff01", "insane", "\u9ed1\u6697", "\u522b\u8bd5"

        return {
            "normality_score": score,
            "verdict": verdict,
            "level": level,
            "label": label,
            "mood": mood,
            "text": f"{verdict}\uff0c\u6b63\u5e38\u5ea6\uff1a{score:g}%",
            "main_ingredients": mains,
            "condiments": condiments,
            "cooking_method": cooking_method,
        }


NormalityService = NormalityScorer

_scorer: Optional[NormalityScorer] = None


def get_scorer() -> NormalityScorer:
    global _scorer
    if _scorer is None:
        _scorer = NormalityScorer()
    return _scorer


def get_normality_service() -> NormalityScorer:
    return get_scorer()
