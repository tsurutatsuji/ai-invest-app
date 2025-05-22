import streamlit as st

st.set_page_config(page_title="設定")
st.title("⚙️ 表示設定")

theme = st.radio("背景色テーマ", ["白", "黒"])
st.success(f"背景を {theme} に設定しました（仮）")
