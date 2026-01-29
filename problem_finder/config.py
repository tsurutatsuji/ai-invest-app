"""
設定ファイル
環境変数からAPI keyを読み込む
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Reddit API設定
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ProblemFinder/1.0")

# Anthropic API設定
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# データベース設定
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "data", "problems.db")

# デフォルトのsubreddit一覧
DEFAULT_SUBREDDITS = [
    "Entrepreneur",
    "SaaS",
    "smallbusiness",
    "startups",
    "productivity",
    "webdev",
    "programming",
]

# スコアリング重み設定
SCORING_WEIGHTS = {
    "popularity": 0.20,      # 言及頻度（upvotes + comments）
    "urgency": 0.15,         # 緊急性
    "ai_suitability": 0.25,  # AI適性
    "vibe_coding_fit": 0.25, # Vibe Coding適性
    "competition": 0.15,     # 競合の少なさ
}

# 取得設定
DEFAULT_FETCH_LIMIT = 25  # 1回の取得で何件取るか
