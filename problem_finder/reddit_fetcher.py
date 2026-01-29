"""
Reddit データ取得モジュール
PRAWを使用してRedditから投稿を取得
"""
import praw
from datetime import datetime
from typing import Optional

from config import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    DEFAULT_FETCH_LIMIT,
)
from database import save_problem, init_database


def get_reddit_client() -> praw.Reddit:
    """Reddit APIクライアントを取得"""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise ValueError(
            "Reddit API credentials not configured. "
            "Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file"
        )

    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


def fetch_subreddit_posts(
    subreddit_name: str,
    sort: str = "hot",
    limit: int = DEFAULT_FETCH_LIMIT,
    time_filter: str = "week",
) -> list:
    """
    指定したsubredditから投稿を取得

    Args:
        subreddit_name: subreddit名（例: "Entrepreneur"）
        sort: ソート方法 ("hot", "new", "top", "rising")
        limit: 取得件数
        time_filter: 期間フィルタ ("hour", "day", "week", "month", "year", "all")
                     ※sortが"top"の場合のみ有効

    Returns:
        投稿データのリスト
    """
    reddit = get_reddit_client()
    subreddit = reddit.subreddit(subreddit_name)

    # ソート方法に応じて投稿を取得
    if sort == "hot":
        posts = subreddit.hot(limit=limit)
    elif sort == "new":
        posts = subreddit.new(limit=limit)
    elif sort == "top":
        posts = subreddit.top(time_filter=time_filter, limit=limit)
    elif sort == "rising":
        posts = subreddit.rising(limit=limit)
    else:
        posts = subreddit.hot(limit=limit)

    results = []
    for post in posts:
        # 問題・悩みを表す投稿をフィルタリング
        # (質問形式や特定のキーワードを含むもの)
        post_data = {
            "reddit_id": post.id,
            "subreddit": subreddit_name,
            "title": post.title,
            "content": post.selftext if post.selftext else "",
            "url": f"https://reddit.com{post.permalink}",
            "upvotes": post.score,
            "comments_count": post.num_comments,
            "reddit_created_at": datetime.fromtimestamp(post.created_utc).isoformat(),
        }
        results.append(post_data)

    return results


def fetch_and_save_posts(
    subreddit_name: str,
    sort: str = "hot",
    limit: int = DEFAULT_FETCH_LIMIT,
    time_filter: str = "week",
) -> dict:
    """
    投稿を取得してデータベースに保存

    Returns:
        取得・保存結果のサマリー
    """
    # DBを初期化（テーブルがない場合に作成）
    init_database()

    posts = fetch_subreddit_posts(subreddit_name, sort, limit, time_filter)

    saved_count = 0
    for post in posts:
        try:
            save_problem(post)
            saved_count += 1
        except Exception as e:
            print(f"Error saving post {post['reddit_id']}: {e}")

    return {
        "subreddit": subreddit_name,
        "fetched": len(posts),
        "saved": saved_count,
        "sort": sort,
        "time_filter": time_filter if sort == "top" else None,
    }


def search_problems_in_subreddit(
    subreddit_name: str,
    query: str = "problem OR issue OR help OR struggling OR frustrated",
    limit: int = DEFAULT_FETCH_LIMIT,
    time_filter: str = "month",
) -> list:
    """
    subreddit内で問題・悩みに関する投稿を検索

    Args:
        subreddit_name: subreddit名
        query: 検索クエリ
        limit: 取得件数
        time_filter: 期間フィルタ

    Returns:
        投稿データのリスト
    """
    reddit = get_reddit_client()
    subreddit = reddit.subreddit(subreddit_name)

    results = []
    for post in subreddit.search(query, sort="relevance", time_filter=time_filter, limit=limit):
        post_data = {
            "reddit_id": post.id,
            "subreddit": subreddit_name,
            "title": post.title,
            "content": post.selftext if post.selftext else "",
            "url": f"https://reddit.com{post.permalink}",
            "upvotes": post.score,
            "comments_count": post.num_comments,
            "reddit_created_at": datetime.fromtimestamp(post.created_utc).isoformat(),
        }
        results.append(post_data)

    return results


if __name__ == "__main__":
    # テスト実行
    print("Testing Reddit fetcher...")
    try:
        result = fetch_and_save_posts("Entrepreneur", limit=5)
        print(f"Result: {result}")
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nTo use this module, create a Reddit App at:")
        print("https://www.reddit.com/prefs/apps")
        print("\nThen set these environment variables in .env:")
        print("REDDIT_CLIENT_ID=your_client_id")
        print("REDDIT_CLIENT_SECRET=your_client_secret")
