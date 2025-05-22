import streamlit as st
import json
import os

st.set_page_config(page_title="プロフィール")
st.title("👤 プロフィール設定")

profile_path = "user_profile.json"

def load_profile():
    if os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"目的": "", "毎月の投資額": "", "性格傾向": "慎重"}

def save_profile(data):
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

profile = load_profile()

with st.form("profile_form"):
    profile["目的"] = st.text_input("目的", profile["目的"])
    profile["毎月の投資額"] = st.text_input("毎月の投資額", profile["毎月の投資額"])
    profile["性格傾向"] = st.selectbox("性格傾向", ["慎重", "攻め", "バランス型"], index=0)
    if st.form_submit_button("保存"):
        save_profile(profile)
        st.success("保存しました")
