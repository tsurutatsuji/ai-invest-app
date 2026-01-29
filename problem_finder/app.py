"""
Problem Finder - Streamlit UI
Redditから問題を収集し、AI適性を分析するダッシュボード
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from config import DEFAULT_SUBREDDITS, DEFAULT_FETCH_LIMIT
from database import (
    init_database,
    get_problems,
    get_analyses_with_problems,
    get_unanalyzed_problems,
    get_category_stats,
)
from reddit_fetcher import fetch_and_save_posts
from analyzer import analyze_and_save, analyze_batch
from scorer import get_score_breakdown, get_score_label, get_score_color

# ページ設定
st.set_page_config(
    page_title="Problem Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# DB初期化
init_database()


def main():
    st.title("🔍 Problem Finder")
    st.markdown("Redditから問題・課題を収集し、AI/Vibe Codingで解決可能なものを発見")

    # サイドバー
    with st.sidebar:
        st.header("⚙️ 設定")

        # Subreddit選択
        selected_subreddit = st.selectbox(
            "Subreddit",
            DEFAULT_SUBREDDITS,
            index=0,
        )

        # カスタムsubreddit入力
        custom_subreddit = st.text_input(
            "またはカスタムsubreddit",
            placeholder="例: productivity",
        )
        if custom_subreddit:
            selected_subreddit = custom_subreddit

        # 取得設定
        st.subheader("取得設定")
        fetch_limit = st.slider("取得件数", 5, 100, DEFAULT_FETCH_LIMIT)
        sort_option = st.selectbox(
            "ソート",
            ["hot", "new", "top", "rising"],
            index=0,
        )
        time_filter = st.selectbox(
            "期間（topの場合のみ）",
            ["day", "week", "month", "year", "all"],
            index=1,
        )

    # メインコンテンツ - タブ
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 データ取得",
        "🤖 AI分析",
        "📊 ランキング",
        "📈 傾向分析",
    ])

    # タブ1: データ取得
    with tab1:
        st.header("📥 Redditからデータ取得")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.info(f"対象: r/{selected_subreddit} | ソート: {sort_option} | 件数: {fetch_limit}")

        with col2:
            if st.button("🚀 取得開始", type="primary", use_container_width=True):
                with st.spinner(f"r/{selected_subreddit}から取得中..."):
                    try:
                        result = fetch_and_save_posts(
                            selected_subreddit,
                            sort=sort_option,
                            limit=fetch_limit,
                            time_filter=time_filter,
                        )
                        st.success(
                            f"✅ 取得完了: {result['fetched']}件取得、{result['saved']}件保存"
                        )
                    except ValueError as e:
                        st.error(f"❌ 設定エラー: {e}")
                    except Exception as e:
                        st.error(f"❌ 取得エラー: {e}")

        # 取得済みデータ表示
        st.subheader("📋 取得済みデータ")
        problems = get_problems(selected_subreddit, limit=50)

        if problems:
            df = pd.DataFrame(problems)
            df = df[["title", "upvotes", "comments_count", "fetched_at"]]
            df.columns = ["タイトル", "Upvotes", "コメント数", "取得日時"]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("まだデータがありません。上のボタンで取得してください。")

    # タブ2: AI分析
    with tab2:
        st.header("🤖 AI分析")

        unanalyzed = get_unanalyzed_problems(limit=100)
        st.metric("未分析の問題", len(unanalyzed))

        col1, col2 = st.columns(2)

        with col1:
            analyze_count = st.number_input(
                "分析件数",
                min_value=1,
                max_value=min(50, len(unanalyzed)) if unanalyzed else 1,
                value=min(10, len(unanalyzed)) if unanalyzed else 1,
            )

        with col2:
            if st.button("🧠 分析開始", type="primary", disabled=len(unanalyzed) == 0):
                progress_bar = st.progress(0)
                status_text = st.empty()

                analyzed = 0
                valid = 0

                for i, problem in enumerate(unanalyzed[:analyze_count]):
                    status_text.text(f"分析中: {problem['title'][:50]}...")
                    try:
                        result = analyze_and_save(problem)
                        analyzed += 1
                        if result:
                            valid += 1
                    except Exception as e:
                        st.warning(f"分析エラー: {e}")

                    progress_bar.progress((i + 1) / analyze_count)

                status_text.empty()
                st.success(f"✅ 完了: {analyzed}件分析、{valid}件が有効な問題")

        # 未分析リスト
        if unanalyzed:
            st.subheader("📋 未分析の問題")
            for p in unanalyzed[:10]:
                with st.expander(f"👁️ {p['title'][:60]}..."):
                    st.write(f"**Subreddit:** r/{p['subreddit']}")
                    st.write(f"**Upvotes:** {p['upvotes']} | **Comments:** {p['comments_count']}")
                    if p.get("content"):
                        st.write(p["content"][:500] + "..." if len(p.get("content", "")) > 500 else p["content"])

    # タブ3: ランキング
    with tab3:
        st.header("📊 問題ランキング")

        # フィルタ
        col1, col2, col3 = st.columns(3)
        with col1:
            min_score = st.slider("最小スコア", 0, 100, 0)
        with col2:
            show_limit = st.selectbox("表示件数", [10, 25, 50, 100], index=1)
        with col3:
            category_filter = st.selectbox(
                "カテゴリ",
                ["すべて"] + [s["category"] for s in get_category_stats() if s["category"]],
            )

        # ランキング表示
        analyses = get_analyses_with_problems(limit=show_limit, min_score=min_score)

        if category_filter != "すべて":
            analyses = [a for a in analyses if a.get("category") == category_filter]

        if analyses:
            for i, item in enumerate(analyses, 1):
                score = item.get("total_score", 0)
                score_color = get_score_color(score)
                score_label = get_score_label(score)

                with st.container():
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.markdown(f"### {i}. {item['title'][:80]}")
                        st.caption(
                            f"r/{item['subreddit']} | "
                            f"👍 {item['upvotes']} | 💬 {item['comments_count']} | "
                            f"📁 {item.get('category', 'N/A')}"
                        )

                    with col2:
                        st.markdown(
                            f"<div style='text-align:center; padding:10px; "
                            f"background-color:{score_color}; border-radius:10px; color:white;'>"
                            f"<h2 style='margin:0;'>{score:.1f}</h2>"
                            f"<small>{score_label}</small></div>",
                            unsafe_allow_html=True,
                        )

                    # 詳細展開
                    with st.expander("詳細を見る"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write("**問題の要約:**")
                            st.write(item.get("problem_summary", "N/A"))

                            st.write("**推奨アプローチ:**")
                            st.write(item.get("recommended_approach", "N/A"))

                            if item.get("url"):
                                st.markdown(f"[元の投稿を見る]({item['url']})")

                        with col2:
                            st.write("**スコア内訳:**")
                            st.write(f"- AI適性: {item.get('ai_suitability_score', 'N/A')}/10")
                            st.write(f"- Vibe Coding適性: {item.get('vibe_coding_fit', 'N/A')}/10")
                            st.write(f"- 深刻度: {item.get('severity', 'N/A')}/10")
                            st.write(f"- 競合度: {item.get('competition_level', 'N/A')}/10")
                            st.write(f"- 市場規模: {item.get('market_size_estimate', 'N/A')}")

                    st.divider()
        else:
            st.info("分析済みのデータがありません。「AI分析」タブで分析を実行してください。")

    # タブ4: 傾向分析
    with tab4:
        st.header("📈 傾向分析")

        stats = get_category_stats()

        if stats:
            # カテゴリ別チャート
            st.subheader("カテゴリ別問題数")
            df_stats = pd.DataFrame(stats)
            st.bar_chart(df_stats.set_index("category")["count"])

            # カテゴリ別スコア
            st.subheader("カテゴリ別平均スコア")
            col1, col2 = st.columns(2)

            with col1:
                st.write("**AI適性が高いカテゴリ**")
                df_ai = df_stats.sort_values("avg_ai_score", ascending=False).head(5)
                for _, row in df_ai.iterrows():
                    if row["avg_ai_score"]:
                        st.write(f"- {row['category']}: {row['avg_ai_score']:.1f}/10")

            with col2:
                st.write("**Vibe Coding適性が高いカテゴリ**")
                df_vibe = df_stats.sort_values("avg_vibe_score", ascending=False).head(5)
                for _, row in df_vibe.iterrows():
                    if row["avg_vibe_score"]:
                        st.write(f"- {row['category']}: {row['avg_vibe_score']:.1f}/10")

            # 生データ表示
            with st.expander("📊 全カテゴリ統計"):
                st.dataframe(df_stats, use_container_width=True)
        else:
            st.info("まだ傾向分析に十分なデータがありません。")


if __name__ == "__main__":
    main()
