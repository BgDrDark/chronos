import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

FACTOR_KEYS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]

QUESTIONS_PATH = Path(__file__).parent / "data" / "ipip200_questions.json"

_question_cache: list[dict] | None = None


def load_all_questions() -> list[dict]:
    global _question_cache
    if _question_cache is None:
        with open(QUESTIONS_PATH, encoding="utf-8") as f:
            _question_cache = json.load(f)
    return _question_cache


def get_questions_by_ids(ids: list[int]) -> list[dict]:
    pool = load_all_questions()
    lookup = {q["id"]: q for q in pool}
    return [lookup[qid] for qid in ids if qid in lookup]


def score_ipip(answers: list[int], questions: list[dict]) -> dict[str, dict]:
    factor_raw: dict[str, list[int]] = {k: [] for k in FACTOR_KEYS}
    for i, q in enumerate(questions):
        factor = q["factor"]
        score = answers[i] if i < len(answers) else 3
        if q.get("direction") == "reverse":
            score = 6 - score
        factor_raw[factor].append(score)

    results = {}
    for factor in FACTOR_KEYS:
        scores = factor_raw[factor]
        if not scores:
            results[factor] = {"sten": 5, "raw": 0.0, "count": 0}
            continue
        raw_avg = sum(scores) / len(scores)
        raw_total = sum(scores)
        min_possible = len(scores) * 1
        max_possible = len(scores) * 5
        sten = int(round(1 + (raw_total - min_possible) / (max_possible - min_possible) * 9))
        sten = max(1, min(10, sten))
        results[factor] = {"sten": sten, "raw": round(raw_avg, 2), "count": len(scores)}

    return results


def generate_interpretation(scores: dict[str, dict]) -> str:
    labels = {
        "openness": ("Отвореност към нов опит", "Високо ниво на креативност, любопитство и естетическа чувствителност"),
        "conscientiousness": ("Съзнателност", "Организираност, надеждност, спазване на срокове"),
        "extraversion": ("Екстраверсия", "Общителност, енергичност, търсене на социални контакти"),
        "agreeableness": ("Дружелюбност", "Сътрудничество, емпатия, доверие към другите"),
        "neuroticism": ("Невротизъм", "Емоционална нестабилност, тревожност, чувствителност към стрес"),
    }
    lines = []
    for factor in FACTOR_KEYS:
        sten = scores[factor]["sten"]
        name, high_desc = labels[factor]
        if sten >= 8:
            level = "Много висок"
        elif sten >= 6:
            level = "Висок"
        elif sten >= 4:
            level = "Среден"
        else:
            level = "Нисък"
        lines.append(f"{name} ({level}, {sten}/10): {high_desc}")
    return "\n".join(lines)
