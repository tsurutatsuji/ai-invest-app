
import streamlit as st

# スマホ対応：センタリング＆サイドバー折りたたみ
st.set_page_config(
    page_title="AI投資アプリ",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.write("ようこそ！左のサイドバーからアプリの各機能にアクセスできます。")
