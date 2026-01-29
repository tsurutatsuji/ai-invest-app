"""
Claude API 分析モジュール
問題を分析してカテゴリ分類、スコアリングを行う
"""
import json
from typing import Optional
import anthropic

from config import ANTHROPIC_API_KEY
from database import save_analysis, get_unanalyzed_problems


def get_claude_client() -> anthropic.Anthropic:
    """Claude APIクライアントを取得"""
    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "Anthropic API key not configured. "
            "Please set ANTHROPIC_API_KEY in .env file"
        )
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


ANALYSIS_PROMPT = """あなたは問題分析の専門家です。以下のReddit投稿を分析し、ビジネスやプロダクト開発の観点から評価してください。

## 投稿情報
タイトル: {title}
内容: {content}
subreddit: r/{subreddit}
Upvotes: {upvotes}
コメント数: {comments_count}

## 分析指示
この投稿から読み取れる問題・課題を分析し、以下のJSON形式で回答してください。

```json
{{
    "category": "問題のメインカテゴリ（例: 業務効率化、マーケティング、財務管理、顧客管理、人材、技術、コミュニケーション、その他）",
    "subcategory": "より詳細なサブカテゴリ",
    "problem_summary": "問題の要約（日本語で2-3文）",
    "severity": "深刻度（1-10、10が最も深刻）",
    "ai_suitability_score": "AIで解決できる度合い（1-10、10が最もAI向き）",
    "vibe_coding_fit": "Vibe Coding（素早いプロトタイプ開発）で解決できる度合い（1-10）",
    "market_size_estimate": "市場規模の推定（small/medium/large/huge）",
    "competition_level": "既存競合の多さ（1-10、10が最も競合が多い）",
    "existing_solutions": "既存の解決策があれば列挙（なければ空配列）",
    "recommended_approach": "推奨されるアプローチ・ソリューションの方向性（日本語で1-2文）",
    "is_valid_problem": "これが解決すべき問題として妥当かどうか（true/false）",
    "reasoning": "上記スコアの根拠（日本語で簡潔に）"
}}
```

重要な注意:
- 投稿が問題・課題を表していない場合は is_valid_problem を false にしてください
- スコアは1-10の整数で回答してください
- JSON形式のみで回答し、他の説明は不要です
"""


def analyze_problem(problem: dict) -> Optional[dict]:
    """
    問題をClaude APIで分析

    Args:
        problem: 問題データ（title, content, subreddit, upvotes, comments_count）

    Returns:
        分析結果のdict、または分析失敗時はNone
    """
    client = get_claude_client()

    prompt = ANALYSIS_PROMPT.format(
        title=problem.get("title", ""),
        content=problem.get("content", "")[:2000],  # 長すぎる場合は切り詰め
        subreddit=problem.get("subreddit", ""),
        upvotes=problem.get("upvotes", 0),
        comments_count=problem.get("comments_count", 0),
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # レスポンスからJSONを抽出
        response_text = message.content[0].text

        # JSONブロックを抽出（```json ... ``` 形式に対応）
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        analysis = json.loads(json_str)
        return analysis

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response: {response_text[:500]}")
        return None
    except Exception as e:
        print(f"Analysis error: {e}")
        return None


def analyze_and_save(problem: dict) -> Optional[dict]:
    """
    問題を分析してデータベースに保存

    Args:
        problem: 問題データ（id含む）

    Returns:
        分析結果、または失敗時はNone
    """
    analysis = analyze_problem(problem)

    if analysis and analysis.get("is_valid_problem", False):
        # スコアを計算（scorerモジュールで詳細計算するが、ここでは簡易版）
        from scorer import calculate_total_score
        analysis["total_score"] = calculate_total_score(problem, analysis)

        # データベースに保存
        save_analysis(problem["id"], analysis)
        return analysis

    return None


def analyze_batch(limit: int = 10) -> dict:
    """
    未分析の問題をバッチ処理で分析

    Args:
        limit: 処理する問題数

    Returns:
        処理結果のサマリー
    """
    problems = get_unanalyzed_problems(limit)

    results = {
        "total": len(problems),
        "analyzed": 0,
        "valid_problems": 0,
        "failed": 0,
    }

    for problem in problems:
        try:
            analysis = analyze_and_save(problem)
            results["analyzed"] += 1
            if analysis:
                results["valid_problems"] += 1
        except Exception as e:
            print(f"Error analyzing problem {problem['id']}: {e}")
            results["failed"] += 1

    return results


if __name__ == "__main__":
    # テスト
    print("Testing analyzer...")
    test_problem = {
        "id": 1,
        "title": "Struggling to manage customer inquiries efficiently",
        "content": "I run a small e-commerce business and I'm drowning in customer emails. "
                   "It takes me hours every day just to respond to basic questions about shipping and returns. "
                   "Is there any way to automate this without losing the personal touch?",
        "subreddit": "Entrepreneur",
        "upvotes": 45,
        "comments_count": 23,
    }

    try:
        result = analyze_problem(test_problem)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nTo use this module, set ANTHROPIC_API_KEY in .env file")
