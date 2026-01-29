"""
スコアリングモジュール
問題の優先度を計算
"""
import math
from config import SCORING_WEIGHTS


def normalize_popularity(upvotes: int, comments: int) -> float:
    """
    人気度を0-10に正規化

    対数スケールを使用（バイラル投稿の影響を抑える）
    """
    # upvotes と comments を組み合わせたスコア
    raw_score = upvotes + (comments * 2)  # コメントは関心の深さを示すため重み付け

    if raw_score <= 0:
        return 1.0

    # 対数スケールで正規化（1000以上で10に近づく）
    normalized = min(10, 1 + (math.log10(raw_score + 1) * 3))
    return round(normalized, 2)


def normalize_market_size(market_size: str) -> float:
    """市場規模を数値に変換"""
    size_map = {
        "small": 3,
        "medium": 5,
        "large": 7,
        "huge": 10,
    }
    return size_map.get(market_size.lower(), 5)


def invert_competition(competition_level: int) -> float:
    """
    競合レベルを反転（競合が少ないほど高スコア）
    """
    return 11 - min(10, max(1, competition_level))


def calculate_total_score(problem: dict, analysis: dict) -> float:
    """
    総合スコアを計算

    Args:
        problem: 問題データ（upvotes, comments_count等）
        analysis: 分析結果（各種スコア）

    Returns:
        0-100の総合スコア
    """
    weights = SCORING_WEIGHTS

    # 各指標のスコア（0-10スケール）
    scores = {
        "popularity": normalize_popularity(
            problem.get("upvotes", 0),
            problem.get("comments_count", 0)
        ),
        "urgency": min(10, max(1, analysis.get("severity", 5))),
        "ai_suitability": min(10, max(1, analysis.get("ai_suitability_score", 5))),
        "vibe_coding_fit": min(10, max(1, analysis.get("vibe_coding_fit", 5))),
        "competition": invert_competition(analysis.get("competition_level", 5)),
    }

    # 市場規模ボーナス（大きな市場ほどボーナス）
    market_bonus = normalize_market_size(analysis.get("market_size_estimate", "medium")) / 10

    # 重み付き平均を計算
    weighted_sum = sum(
        scores[key] * weights[key]
        for key in weights.keys()
    )

    # 0-100スケールに変換し、市場規模ボーナスを加算
    total_score = (weighted_sum * 10) * (1 + market_bonus * 0.1)

    return round(min(100, total_score), 2)


def get_score_breakdown(problem: dict, analysis: dict) -> dict:
    """
    スコアの内訳を取得

    Args:
        problem: 問題データ
        analysis: 分析結果

    Returns:
        各指標のスコアと重みの詳細
    """
    weights = SCORING_WEIGHTS

    popularity = normalize_popularity(
        problem.get("upvotes", 0),
        problem.get("comments_count", 0)
    )
    urgency = min(10, max(1, analysis.get("severity", 5)))
    ai_suitability = min(10, max(1, analysis.get("ai_suitability_score", 5)))
    vibe_coding_fit = min(10, max(1, analysis.get("vibe_coding_fit", 5)))
    competition = invert_competition(analysis.get("competition_level", 5))
    market_size = normalize_market_size(analysis.get("market_size_estimate", "medium"))

    return {
        "popularity": {
            "score": popularity,
            "weight": weights["popularity"],
            "weighted": round(popularity * weights["popularity"], 2),
            "description": "Upvotes + コメント数から算出",
        },
        "urgency": {
            "score": urgency,
            "weight": weights["urgency"],
            "weighted": round(urgency * weights["urgency"], 2),
            "description": "問題の深刻度（AI判定）",
        },
        "ai_suitability": {
            "score": ai_suitability,
            "weight": weights["ai_suitability"],
            "weighted": round(ai_suitability * weights["ai_suitability"], 2),
            "description": "AIで解決しやすいか",
        },
        "vibe_coding_fit": {
            "score": vibe_coding_fit,
            "weight": weights["vibe_coding_fit"],
            "weighted": round(vibe_coding_fit * weights["vibe_coding_fit"], 2),
            "description": "素早くプロト作成できるか",
        },
        "competition": {
            "score": competition,
            "weight": weights["competition"],
            "weighted": round(competition * weights["competition"], 2),
            "description": "競合の少なさ",
        },
        "market_size": {
            "score": market_size,
            "raw": analysis.get("market_size_estimate", "medium"),
            "description": "市場規模（ボーナス係数）",
        },
        "total_score": calculate_total_score(problem, analysis),
    }


def rank_problems(problems_with_analyses: list) -> list:
    """
    問題リストをスコア順にランキング

    Args:
        problems_with_analyses: 問題と分析結果の結合リスト

    Returns:
        スコア降順でソートされたリスト
    """
    return sorted(
        problems_with_analyses,
        key=lambda x: x.get("total_score", 0),
        reverse=True
    )


def get_score_label(score: float) -> str:
    """スコアに応じたラベルを返す"""
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Very Good"
    elif score >= 50:
        return "Good"
    elif score >= 35:
        return "Fair"
    else:
        return "Low"


def get_score_color(score: float) -> str:
    """スコアに応じた色を返す（Streamlit用）"""
    if score >= 80:
        return "#10B981"  # green
    elif score >= 65:
        return "#3B82F6"  # blue
    elif score >= 50:
        return "#F59E0B"  # yellow
    elif score >= 35:
        return "#F97316"  # orange
    else:
        return "#EF4444"  # red


if __name__ == "__main__":
    # テスト
    test_problem = {
        "upvotes": 150,
        "comments_count": 45,
    }

    test_analysis = {
        "severity": 7,
        "ai_suitability_score": 8,
        "vibe_coding_fit": 9,
        "competition_level": 4,
        "market_size_estimate": "large",
    }

    breakdown = get_score_breakdown(test_problem, test_analysis)
    print("Score Breakdown:")
    for key, value in breakdown.items():
        if isinstance(value, dict):
            print(f"  {key}: {value.get('score', value.get('raw', ''))} "
                  f"(weight: {value.get('weight', 'N/A')})")
        else:
            print(f"  {key}: {value}")
