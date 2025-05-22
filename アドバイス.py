
import streamlit as st
import os
import json
import datetime
from dotenv import load_dotenv
from openai import OpenAI

# 初期化
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROFILE_PATH = "user_profile.json"
CHAT_LOG_PATH = "chat_log.json"

# プロファイル読み込み
def load_user_profile():
    default = {
        "name": "ユーザー",
        "goal": "資産1億円",
        "personality": "誠実で親身",
        "目的": "",
        "現在の資産": "",
        "毎月の投資額": "",
        "収入目標": "",
        "投資経験": "初心者",
        "性格傾向": "慎重"
    }
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            return {**default, **loaded}
    return default

# チャットログ読み込み
def load_chat_log():
    if os.path.exists(CHAT_LOG_PATH):
        with open(CHAT_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# チャットログ保存
def save_chat_log(chat_log):
    with open(CHAT_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(chat_log, f, ensure_ascii=False, indent=2)

# 入力分類
def classify_input(text):
    text = text.lower()
    if any(word in text for word in ["おすすめ", "何買えば", "投資", "どうしたら", "銘柄"]):
        return "advice"
    elif any(word in text for word in ["疲れた", "不安", "つらい", "うれしい", "寂しい", "悲しい"]):
        return "empathy"
    elif any(word in text for word in ["雑談", "最近どう", "話そう", "暇", "日常"]):
        return "chat"
    else:
        return "general"

# 軽量プロンプト生成（発言回数に応じて段階的に重くする）
def build_prompt_light(profile, user_input, turn_count):
    base = f"""あなたはウォーレン・バフェットの哲学をベースにした、親身な投資AIです。
以下のプロフィールに基づいて対応してください：

- 目的: {profile["目的"]}
- 現在の資産: {profile["現在の資産"]}
- 毎月の投資額: {profile["毎月の投資額"]}
- 収入目標: {profile["収入目標"]}
- 投資経験: {profile["投資経験"]}
- 性格傾向: {profile["性格傾向"]}

ユーザーの入力:
「{user_input}」
"""
    if turn_count == 1:
        return base + "\n\n最初の応答はやさしく問いかけるだけにしてください。アドバイスは後に続けます。"
    elif turn_count == 2:
        return base + "\n\nプロフィールをもとに軽く方向性を示しながら、まだ深入りしすぎないようにしてください。"
    else:
        return base + "\n\n本格的な分析・提案を含めても構いません。バフェットの語録や例え話を交えても良いです。"

# Streamlit UI
st.set_page_config(page_title="投資アドバイス")
st.title("💬 投資アドバイス")

# ステート初期化
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0

# ロード
profile = load_user_profile()
chat_log = load_chat_log()

# 入力
user_input = st.chat_input("投資について相談する")

if user_input:
    st.session_state.turn_count += 1
    category = classify_input(user_input)
    prompt = build_prompt_light(profile, user_input, st.session_state.turn_count)

    # OpenAI 応答
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}]
    )
    reply = res.choices[0].message.content.strip()

    # 表示と保存
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    chat_log.append({
        "date": datetime.datetime.now().isoformat(),
        "input": user_input,
        "response": reply
    })
    save_chat_log(chat_log)

# チャット履歴表示
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])
