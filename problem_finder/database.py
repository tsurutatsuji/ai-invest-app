"""
データベース操作モジュール
SQLiteを使用して問題と分析結果を保存
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from config import DATABASE_PATH


def get_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """コンテキストマネージャーでDB接続を管理"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_database():
    """データベースの初期化（テーブル作成）"""
    with get_db() as conn:
        cursor = conn.cursor()

        # 問題テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reddit_id TEXT UNIQUE,
                subreddit TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                url TEXT,
                upvotes INTEGER DEFAULT 0,
                comments_count INTEGER DEFAULT 0,
                reddit_created_at TIMESTAMP,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 分析結果テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id INTEGER NOT NULL,
                category TEXT,
                subcategory TEXT,
                problem_summary TEXT,
                severity INTEGER,
                ai_suitability_score INTEGER,
                vibe_coding_fit INTEGER,
                market_size_estimate TEXT,
                competition_level INTEGER,
                existing_solutions TEXT,
                recommended_approach TEXT,
                total_score REAL,
                analysis_json TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (problem_id) REFERENCES problems(id)
            )
        """)

        # 傾向分析テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period_start DATE,
                period_end DATE,
                subreddit TEXT,
                top_categories TEXT,
                emerging_problems TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # インデックス作成
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_problems_subreddit ON problems(subreddit)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_problems_fetched ON problems(fetched_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_score ON analyses(total_score DESC)")


def save_problem(problem_data: dict) -> int:
    """問題をデータベースに保存"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO problems
            (reddit_id, subreddit, title, content, url, upvotes, comments_count, reddit_created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            problem_data.get("reddit_id"),
            problem_data.get("subreddit"),
            problem_data.get("title"),
            problem_data.get("content"),
            problem_data.get("url"),
            problem_data.get("upvotes", 0),
            problem_data.get("comments_count", 0),
            problem_data.get("reddit_created_at"),
        ))
        return cursor.lastrowid


def save_analysis(problem_id: int, analysis_data: dict) -> int:
    """分析結果をデータベースに保存"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analyses
            (problem_id, category, subcategory, problem_summary, severity,
             ai_suitability_score, vibe_coding_fit, market_size_estimate,
             competition_level, existing_solutions, recommended_approach,
             total_score, analysis_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            problem_id,
            analysis_data.get("category"),
            analysis_data.get("subcategory"),
            analysis_data.get("problem_summary"),
            analysis_data.get("severity"),
            analysis_data.get("ai_suitability_score"),
            analysis_data.get("vibe_coding_fit"),
            analysis_data.get("market_size_estimate"),
            analysis_data.get("competition_level"),
            analysis_data.get("existing_solutions"),
            analysis_data.get("recommended_approach"),
            analysis_data.get("total_score"),
            json.dumps(analysis_data, ensure_ascii=False),
        ))
        return cursor.lastrowid


def get_problems(subreddit: Optional[str] = None, limit: int = 100) -> list:
    """問題一覧を取得"""
    with get_db() as conn:
        cursor = conn.cursor()
        if subreddit:
            cursor.execute("""
                SELECT * FROM problems
                WHERE subreddit = ?
                ORDER BY fetched_at DESC
                LIMIT ?
            """, (subreddit, limit))
        else:
            cursor.execute("""
                SELECT * FROM problems
                ORDER BY fetched_at DESC
                LIMIT ?
            """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_analyses_with_problems(limit: int = 50, min_score: float = 0) -> list:
    """分析結果と問題を結合して取得（スコア順）"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                p.id as problem_id,
                p.subreddit,
                p.title,
                p.content,
                p.url,
                p.upvotes,
                p.comments_count,
                p.fetched_at,
                a.id as analysis_id,
                a.category,
                a.subcategory,
                a.problem_summary,
                a.severity,
                a.ai_suitability_score,
                a.vibe_coding_fit,
                a.market_size_estimate,
                a.competition_level,
                a.existing_solutions,
                a.recommended_approach,
                a.total_score,
                a.analyzed_at
            FROM analyses a
            JOIN problems p ON a.problem_id = p.id
            WHERE a.total_score >= ?
            ORDER BY a.total_score DESC
            LIMIT ?
        """, (min_score, limit))
        return [dict(row) for row in cursor.fetchall()]


def get_unanalyzed_problems(limit: int = 50) -> list:
    """未分析の問題を取得"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.* FROM problems p
            LEFT JOIN analyses a ON p.id = a.problem_id
            WHERE a.id IS NULL
            ORDER BY p.upvotes DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_category_stats() -> list:
    """カテゴリ別の統計を取得"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                category,
                COUNT(*) as count,
                AVG(total_score) as avg_score,
                AVG(ai_suitability_score) as avg_ai_score,
                AVG(vibe_coding_fit) as avg_vibe_score
            FROM analyses
            GROUP BY category
            ORDER BY count DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_trend_data(days: int = 30) -> list:
    """指定日数の傾向データを取得"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                DATE(p.fetched_at) as date,
                a.category,
                COUNT(*) as count,
                AVG(a.total_score) as avg_score
            FROM analyses a
            JOIN problems p ON a.problem_id = p.id
            WHERE p.fetched_at >= DATE('now', ?)
            GROUP BY DATE(p.fetched_at), a.category
            ORDER BY date DESC, count DESC
        """, (f'-{days} days',))
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    # 直接実行された場合はDBを初期化
    init_database()
    print(f"Database initialized at: {DATABASE_PATH}")
