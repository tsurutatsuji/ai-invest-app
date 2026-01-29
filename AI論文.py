import streamlit as st
import requests
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(
    page_title="AI論文コレクター",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("AI論文コレクター")
st.caption("arXivからAI関連の最新論文を収集・リスト化します")

# 保存ファイルのパス
FAVORITES_FILE = "favorite_papers.json"

# お気に入り論文の読み込み
def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# お気に入り論文の保存
def save_favorites(favorites):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)

# arXiv APIから論文を取得
def fetch_arxiv_papers(query, category, max_results=20, sort_by="submittedDate", sort_order="descending"):
    base_url = "http://export.arxiv.org/api/query?"

    # 検索クエリの構築
    search_parts = []
    if query:
        search_parts.append(f"all:{query}")
    if category != "すべて":
        cat_map = {
            "人工知能 (cs.AI)": "cs.AI",
            "機械学習 (cs.LG)": "cs.LG",
            "自然言語処理 (cs.CL)": "cs.CL",
            "コンピュータビジョン (cs.CV)": "cs.CV",
            "ニューラルネットワーク (cs.NE)": "cs.NE",
            "ロボティクス (cs.RO)": "cs.RO",
            "統計的機械学習 (stat.ML)": "stat.ML"
        }
        if category in cat_map:
            search_parts.append(f"cat:{cat_map[category]}")

    if not search_parts:
        search_parts.append("cat:cs.AI OR cat:cs.LG OR cat:cs.CL")

    search_query = " AND ".join(search_parts)

    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order
    }

    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        return parse_arxiv_response(response.text)
    except requests.RequestException as e:
        st.error(f"論文の取得に失敗しました: {e}")
        return []

# arXiv XMLレスポンスの解析
def parse_arxiv_response(xml_text):
    papers = []
    root = ET.fromstring(xml_text)

    # 名前空間の定義
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }

    for entry in root.findall('atom:entry', ns):
        paper = {}

        # タイトル
        title_elem = entry.find('atom:title', ns)
        paper['title'] = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else "不明"

        # 要約
        summary_elem = entry.find('atom:summary', ns)
        paper['summary'] = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None else ""

        # 著者
        authors = []
        for author in entry.findall('atom:author', ns):
            name_elem = author.find('atom:name', ns)
            if name_elem is not None:
                authors.append(name_elem.text)
        paper['authors'] = authors

        # ID (arXiv ID)
        id_elem = entry.find('atom:id', ns)
        paper['id'] = id_elem.text if id_elem is not None else ""
        paper['arxiv_id'] = paper['id'].split('/')[-1] if paper['id'] else ""

        # リンク
        for link in entry.findall('atom:link', ns):
            if link.get('type') == 'application/pdf':
                paper['pdf_url'] = link.get('href')
            elif link.get('rel') == 'alternate':
                paper['url'] = link.get('href')

        # 公開日
        published_elem = entry.find('atom:published', ns)
        if published_elem is not None:
            paper['published'] = published_elem.text[:10]
        else:
            paper['published'] = ""

        # 更新日
        updated_elem = entry.find('atom:updated', ns)
        if updated_elem is not None:
            paper['updated'] = updated_elem.text[:10]
        else:
            paper['updated'] = ""

        # カテゴリ
        categories = []
        for category in entry.findall('atom:category', ns):
            term = category.get('term')
            if term:
                categories.append(term)
        paper['categories'] = categories

        papers.append(paper)

    return papers

# セッション状態の初期化
if 'papers' not in st.session_state:
    st.session_state.papers = []
if 'favorites' not in st.session_state:
    st.session_state.favorites = load_favorites()

# サイドバー: 検索オプション
st.sidebar.header("検索設定")

search_query = st.sidebar.text_input(
    "キーワード検索",
    placeholder="例: transformer, GPT, diffusion",
    help="論文のタイトル、要約、著者などを検索"
)

category = st.sidebar.selectbox(
    "カテゴリ",
    [
        "すべて",
        "人工知能 (cs.AI)",
        "機械学習 (cs.LG)",
        "自然言語処理 (cs.CL)",
        "コンピュータビジョン (cs.CV)",
        "ニューラルネットワーク (cs.NE)",
        "ロボティクス (cs.RO)",
        "統計的機械学習 (stat.ML)"
    ]
)

max_results = st.sidebar.slider("取得件数", min_value=5, max_value=50, value=20)

sort_by = st.sidebar.selectbox(
    "並び替え",
    ["投稿日", "最終更新日", "関連度"],
    index=0
)

sort_map = {
    "投稿日": "submittedDate",
    "最終更新日": "lastUpdatedDate",
    "関連度": "relevance"
}

# 検索ボタン
if st.sidebar.button("論文を検索", type="primary", use_container_width=True):
    with st.spinner("arXivから論文を取得中..."):
        st.session_state.papers = fetch_arxiv_papers(
            search_query,
            category,
            max_results,
            sort_map[sort_by]
        )
    if st.session_state.papers:
        st.sidebar.success(f"{len(st.session_state.papers)}件の論文を取得しました")
    else:
        st.sidebar.warning("論文が見つかりませんでした")

# タブの作成
tab1, tab2 = st.tabs(["検索結果", "お気に入り"])

with tab1:
    if not st.session_state.papers:
        st.info("左のサイドバーから検索条件を設定して、「論文を検索」ボタンをクリックしてください。")

        # デフォルトで最新のAI論文を表示
        if st.button("最新のAI論文を表示"):
            with st.spinner("最新論文を取得中..."):
                st.session_state.papers = fetch_arxiv_papers("", "すべて", 20)
            st.rerun()
    else:
        st.subheader(f"検索結果: {len(st.session_state.papers)}件")

        for i, paper in enumerate(st.session_state.papers):
            with st.expander(f"{paper['title']}", expanded=i < 3):
                col1, col2 = st.columns([3, 1])

                with col1:
                    # 著者
                    if paper['authors']:
                        authors_str = ", ".join(paper['authors'][:5])
                        if len(paper['authors']) > 5:
                            authors_str += f" 他{len(paper['authors'])-5}名"
                        st.caption(f"著者: {authors_str}")

                    # 日付とカテゴリ
                    meta_info = []
                    if paper['published']:
                        meta_info.append(f"公開日: {paper['published']}")
                    if paper['categories']:
                        meta_info.append(f"カテゴリ: {', '.join(paper['categories'][:3])}")
                    if meta_info:
                        st.caption(" | ".join(meta_info))

                    # 要約
                    st.markdown("**要約:**")
                    summary = paper['summary']
                    if len(summary) > 500:
                        summary = summary[:500] + "..."
                    st.write(summary)

                with col2:
                    # リンクボタン
                    if paper.get('url'):
                        st.link_button("arXivで見る", paper['url'], use_container_width=True)
                    if paper.get('pdf_url'):
                        st.link_button("PDFをダウンロード", paper['pdf_url'], use_container_width=True)

                    # お気に入りボタン
                    is_favorite = any(f['arxiv_id'] == paper['arxiv_id'] for f in st.session_state.favorites)

                    if is_favorite:
                        if st.button("お気に入りから削除", key=f"unfav_{i}", use_container_width=True):
                            st.session_state.favorites = [f for f in st.session_state.favorites if f['arxiv_id'] != paper['arxiv_id']]
                            save_favorites(st.session_state.favorites)
                            st.rerun()
                    else:
                        if st.button("お気に入りに追加", key=f"fav_{i}", use_container_width=True):
                            st.session_state.favorites.append(paper)
                            save_favorites(st.session_state.favorites)
                            st.success("お気に入りに追加しました!")
                            st.rerun()

with tab2:
    st.subheader(f"お気に入り: {len(st.session_state.favorites)}件")

    if not st.session_state.favorites:
        st.info("お気に入りの論文はまだありません。検索結果から論文を追加してください。")
    else:
        # エクスポートオプション
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            # CSV出力
            df = pd.DataFrame([{
                'タイトル': p['title'],
                '著者': ', '.join(p['authors']),
                '公開日': p['published'],
                'arXiv ID': p['arxiv_id'],
                'URL': p.get('url', ''),
                'PDF URL': p.get('pdf_url', ''),
                'カテゴリ': ', '.join(p.get('categories', []))
            } for p in st.session_state.favorites])

            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "CSVでエクスポート",
                csv,
                "ai_papers.csv",
                "text/csv",
                use_container_width=True
            )

        with col2:
            # JSON出力
            json_str = json.dumps(st.session_state.favorites, ensure_ascii=False, indent=2)
            st.download_button(
                "JSONでエクスポート",
                json_str,
                "ai_papers.json",
                "application/json",
                use_container_width=True
            )

        st.divider()

        # お気に入り一覧
        for i, paper in enumerate(st.session_state.favorites):
            with st.expander(f"{paper['title']}", expanded=False):
                col1, col2 = st.columns([3, 1])

                with col1:
                    if paper.get('authors'):
                        authors_str = ", ".join(paper['authors'][:5])
                        if len(paper['authors']) > 5:
                            authors_str += f" 他{len(paper['authors'])-5}名"
                        st.caption(f"著者: {authors_str}")

                    meta_info = []
                    if paper.get('published'):
                        meta_info.append(f"公開日: {paper['published']}")
                    if paper.get('categories'):
                        meta_info.append(f"カテゴリ: {', '.join(paper['categories'][:3])}")
                    if meta_info:
                        st.caption(" | ".join(meta_info))

                    if paper.get('summary'):
                        st.markdown("**要約:**")
                        summary = paper['summary']
                        if len(summary) > 500:
                            summary = summary[:500] + "..."
                        st.write(summary)

                with col2:
                    if paper.get('url'):
                        st.link_button("arXivで見る", paper['url'], use_container_width=True)
                    if paper.get('pdf_url'):
                        st.link_button("PDFをダウンロード", paper['pdf_url'], use_container_width=True)

                    if st.button("削除", key=f"del_fav_{i}", type="secondary", use_container_width=True):
                        st.session_state.favorites = [f for f in st.session_state.favorites if f['arxiv_id'] != paper['arxiv_id']]
                        save_favorites(st.session_state.favorites)
                        st.rerun()

# フッター
st.divider()
st.caption("データソース: arXiv.org API | AI論文コレクター")
