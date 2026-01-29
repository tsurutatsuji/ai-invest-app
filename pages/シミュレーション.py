
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# 日本語フォント設定（環境に応じて変更可）
matplotlib.rcParams['font.family'] = 'Meiryo'

st.set_page_config(page_title="シミュレーション")
st.title("📈 資産シミュレーション")

# 金額の表示変換関数
def format_yen(value):
    if value >= 1e8:
        return f"{value/1e8:.1f} 億円"
    elif value >= 1e4:
        return f"{value/1e4:.1f} 万円"
    else:
        return f"{int(value):,} 円"

initial = st.number_input("初期投資額", value=0, step=10000)
monthly = st.number_input("毎月の投資額", value=30000, step=1000)
years = st.slider("投資年数", 1, 100, 20)
rate = st.slider("年利（％）", 1.0, 15.0, 5.0)

r = (rate / 100) / 12
n = years * 12

# 将来資産額の計算
future = initial * (1 + r)**n + monthly * ((1 + r)**n - 1) / r if r > 0 else initial + monthly * n
st.metric("将来資産額", format_yen(future))

# 資産推移グラフ
st.subheader("📊 資産推移グラフ（複利）")
months = np.arange(1, n + 1)
values = [initial * (1 + r)**i + monthly * ((1 + r)**i - 1) / r for i in months]


fig, ax = plt.subplots(figsize=(8, 4))

# 貯金（利子なし）シミュレーション
savings = [initial + monthly * i for i in months]
ax.plot(months / 12, savings, label="貯金（利子なし）", color="gray", linestyle="--")

ax.plot(months / 12, values, label=f"年利 {rate:.1f}%", color="blue")
ax.set_xlabel("運用年数")
ax.set_ylabel("資産額（円）")
ax.set_title("積立 + 初期投資 による資産推移（貯金と比較）")
ax.grid(True)
ax.legend()

# y軸ラベルを日本語表記に
from matplotlib.ticker import FuncFormatter
def yen_formatter(x, pos):
    if x >= 1e8:
        return f"{x/1e8:.1f}億"
    elif x >= 1e4:
        return f"{x/1e4:.0f}万"
    else:
        return f"{int(x):,}"

ax.yaxis.set_major_formatter(FuncFormatter(yen_formatter))

st.pyplot(fig)
