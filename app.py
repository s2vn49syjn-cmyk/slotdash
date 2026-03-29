"""
スロダッシュ v2 - Google Sheets連携版
スーパーコスモ堺専用 / スマホ最適化 / メモ・星印機能付き
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import re
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ─────────────────────────────────────────────
# ページ設定
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="スロダッシュ | コスモ堺",
    page_icon="🎰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# ★ 設定（書き換えてください）
# ─────────────────────────────────────────────
SPREADSHEET_ID = "1Hak9Q7Q_kjbp22A59pAUJ2twrEy4mdXk1sBfLYlynR8"
SHEET_NAME = "スロデータ"

# ─────────────────────────────────────────────
# CSS（ネオン調ダークテーマ）
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+JP:wght@300;400;700&display=swap');

html, body, [class*="css"] {
    background-color: #0a0e1a !important;
    color: #e0e6f0 !important;
    font-family: 'Noto Sans JP', sans-serif !important;
}
.main .block-container {
    padding: 0.5rem 1rem 2rem 1rem !important;
    max-width: 480px !important;
    margin: auto !important;
}
.neon-title {
    font-family: 'Orbitron', monospace;
    font-size: 1.5rem;
    font-weight: 900;
    color: #00ffcc;
    text-shadow: 0 0 10px #00ffcc88, 0 0 30px #00ffcc44;
    letter-spacing: 2px;
    margin: 0;
}
.neon-sub { font-size: 0.7rem; color: #7a8aaa; letter-spacing: 1px; }
.header-bar {
    background: linear-gradient(135deg, #0f1729 0%, #141c30 100%);
    border-bottom: 1px solid #00ffcc33;
    padding: 0.8rem 1rem;
    margin: -0.5rem -1rem 1rem -1rem;
    box-shadow: 0 4px 20px #00ffcc11;
}
.card {
    background: linear-gradient(135deg, #111828 0%, #0d1520 100%);
    border: 1px solid #1e2d45;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.8rem;
    position: relative;
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00ffcc66, transparent);
}
.card-hot::before { background: linear-gradient(90deg, transparent, #00ff8866, transparent); }
.card-cold::before { background: linear-gradient(90deg, transparent, #ff444466, transparent); }
.machine-num { font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #7a8aaa; }
.machine-name { font-size: 1rem; font-weight: 700; color: #c8d8f0; margin: 2px 0 6px; }
.diff-plus { font-family: 'Orbitron', monospace; font-size: 1.5rem; font-weight: 900; color: #00ff88; text-shadow: 0 0 8px #00ff8866; }
.diff-minus { font-family: 'Orbitron', monospace; font-size: 1.5rem; font-weight: 900; color: #ff4444; text-shadow: 0 0 8px #ff444466; }
.diff-neutral { font-family: 'Orbitron', monospace; font-size: 1.5rem; font-weight: 900; color: #ffcc00; }
.score-bar-wrap { background: #0a0e1a; border-radius: 6px; height: 6px; margin-top: 6px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 6px; }
.badge { display: inline-block; font-size: 0.65rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; margin-right: 4px; }
.badge-hot { background: #00ff8822; color: #00ff88; border: 1px solid #00ff8844; }
.badge-cold { background: #ff444422; color: #ff6666; border: 1px solid #ff444444; }
.badge-star { background: #ffcc0022; color: #ffcc00; border: 1px solid #ffcc0044; }
.badge-juggler { background: #8844ff22; color: #aa88ff; border: 1px solid #8844ff44; }
.section-title {
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    color: #00ffcc;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 1.2rem 0 0.6rem;
    padding-bottom: 4px;
    border-bottom: 1px solid #00ffcc22;
}
.memo-box {
    background: #0d1520;
    border: 1px solid #1e2d45;
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 0.8rem;
    color: #a0b8d0;
    margin-top: 6px;
}
.stButton > button {
    background: #111828 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 8px !important;
    color: #a0b0cc !important;
    font-size: 0.75rem !important;
    padding: 0.4rem 0.5rem !important;
    width: 100% !important;
}
.stButton > button:hover { border-color: #00ffcc66 !important; color: #00ffcc !important; }
.stTabs [data-baseweb="tab-list"] { background: #0d1520 !important; border-radius: 10px !important; gap: 4px; padding: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px !important; color: #7a8aaa !important; font-size: 0.8rem !important; }
.stTabs [aria-selected="true"] { background: #1e2d45 !important; color: #00ffcc !important; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background-color: #111828 !important;
    border: 1px solid #1e2d45 !important;
    color: #e0e6f0 !important;
    border-radius: 8px !important;
}
[data-testid="stMetric"] { background: #111828; border: 1px solid #1e2d45; border-radius: 10px; padding: 0.6rem 0.8rem; }
[data-testid="stMetricLabel"] { font-size: 0.7rem !important; color: #7a8aaa !important; }
[data-testid="stMetricValue"] { font-family: 'Orbitron', monospace !important; font-size: 1rem !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #1e2d45; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────────
JUGGLER_KEYWORDS = ["ジャグラー", "juggler", "JUGGLER"]

def parse_num(val):
    if pd.isna(val) or str(val).strip() in ["-", "", "None"]:
        return np.nan
    s = str(val).strip().replace(",", "").replace("＋", "+").replace("－", "-")
    m = re.search(r"[+-]?\d+", s)
    return float(m.group()) if m else np.nan

def diff_sign(val):
    if np.isnan(val): return "-"
    return f"+{int(val):,}" if val >= 0 else f"{int(val):,}"

def diff_class(val):
    if np.isnan(val): return "diff-neutral"
    return "diff-plus" if val >= 0 else "diff-minus"

def score_color(s):
    if s >= 70: return "#00ff88"
    if s >= 50: return "#ffcc00"
    return "#ff4444"

def is_juggler(name):
    return any(k in str(name) for k in JUGGLER_KEYWORDS)

def calc_score(diff, week_avg, trend_up):
    score = 50.0
    if not np.isnan(diff): score += np.clip(diff / 1000 * 30, -30, 30)
    if not np.isnan(week_avg): score += np.clip(week_avg / 500 * 20, -20, 20)
    if trend_up is True: score += 10
    elif trend_up is False: score -= 10
    return float(np.clip(score, 0, 100))

# ─────────────────────────────────────────────
# Google Sheets読み込み
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)  # 5分キャッシュ
def load_from_sheets():
    """Google SheetsからDataFrameを取得（5分キャッシュ）"""
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(SHEET_NAME)
        data = sheet.get_all_records()
        if not data:
            return None, "シートにデータがありません"
        df = pd.DataFrame(data)
        return df, None
    except Exception as e:
        return None, str(e)

def process_df(df_raw):
    """生DataFrameを整形"""
    df = pd.DataFrame()

    # 列名マッピング（柔軟対応）
    cols = {c.strip(): c for c in df_raw.columns}

    def find_col(*keys):
        for k in keys:
            for c in cols:
                if k in c:
                    return cols[c]
        return None

    台番col = find_col("台番", "台no", "No")
    機種col = find_col("機種名", "機種", "name")
    差枚col = find_col("前日差枚", "差枚")
    回転col = find_col("回転数", "回転", "games")
    ボーナスcol = find_col("ボーナス", "bonus")

    if 台番col is None or 機種col is None:
        return None, None

    df["台番"] = df_raw[台番col].apply(parse_num)
    df["機種名"] = df_raw[機種col].astype(str).str.strip()
    df["前日差枚"] = df_raw[差枚col].apply(parse_num) if 差枚col else np.nan
    df["回転数"] = df_raw[回転col].apply(parse_num) if 回転col else np.nan
    df["ボーナス"] = df_raw[ボーナスcol].apply(parse_num) if ボーナスcol else np.nan

    # 週次データ（N日前差枚列）
    week_cols = []
    day_labels = []
    for col in df_raw.columns:
        m = re.search(r"(\d+)日前差枚", col)
        if m:
            week_cols.append((int(m.group(1)), col))
    week_cols.sort(key=lambda x: x[0], reverse=True)

    weekly_df = pd.DataFrame()
    if week_cols:
        labels = [f"-{d}日" for d, _ in week_cols]
        for (d, col), label in zip(week_cols, labels):
            weekly_df[label] = df_raw[col].apply(parse_num)
        weekly_df.index = df.index

    # 週平均・スコア計算
    if not weekly_df.empty:
        df["週平均"] = weekly_df.mean(axis=1)
        trend_list = []
        for idx in weekly_df.index:
            vals = weekly_df.loc[idx].dropna().values
            if len(vals) >= 3:
                trend_list.append(vals[-1] > vals[0])
            else:
                trend_list.append(None)
        df["スコア"] = [calc_score(df.loc[i, "前日差枚"], df.loc[i, "週平均"], trend_list[i]) for i in df.index]
    else:
        df["週平均"] = df["前日差枚"]
        df["スコア"] = [calc_score(df.loc[i, "前日差枚"], np.nan, None) for i in df.index]

    df["is_juggler"] = df["機種名"].apply(is_juggler)
    df.index = range(len(df))
    if not weekly_df.empty:
        weekly_df.index = range(len(weekly_df))

    return df, weekly_df

# ─────────────────────────────────────────────
# セッションステート初期化
# ─────────────────────────────────────────────
if "stars" not in st.session_state:
    st.session_state.stars = {}      # {台番: True/False}
if "memos" not in st.session_state:
    st.session_state.memos = {}      # {台番: "メモ文字列"}
if "active_filter" not in st.session_state:
    st.session_state.active_filter = "全台"
if "df_main" not in st.session_state:
    st.session_state.df_main = None
if "df_weekly" not in st.session_state:
    st.session_state.df_weekly = None
if "last_updated" not in st.session_state:
    st.session_state.last_updated = None

# ─────────────────────────────────────────────
# データロード（起動時 + 更新ボタン）
# ─────────────────────────────────────────────
def load_data():
    with st.spinner("データ取得中..."):
        df_raw, err = load_from_sheets()
        if err:
            st.error(f"❌ {err}")
            return
        df, wdf = process_df(df_raw)
        if df is None:
            st.error("❌ データの列が認識できませんでした")
            return
        st.session_state.df_main = df
        st.session_state.df_weekly = wdf if wdf is not None else pd.DataFrame()
        st.session_state.last_updated = datetime.now().strftime("%H:%M")

# 初回ロード
if st.session_state.df_main is None:
    load_data()

# ─────────────────────────────────────────────
# ヘッダー
# ─────────────────────────────────────────────
today_str = datetime.now().strftime("%Y年%-m月%-d日")
updated_str = st.session_state.last_updated or "-"

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f"""
    <div class="header-bar">
      <div class="neon-title">🎰 SLOTDASH</div>
      <div class="neon-sub">{today_str} &nbsp;|&nbsp; コスモ堺&nbsp; 更新:{updated_str}</div>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
    if st.button("🔄 更新", use_container_width=True):
        st.cache_data.clear()
        load_data()
        st.rerun()

# ─────────────────────────────────────────────
# タブ
# ─────────────────────────────────────────────
tab_home, tab_trend, tab_all, tab_memo = st.tabs(["🏠 ホーム", "📈 トレンド", "📋 全台", "⭐ メモ"])

# ════════════════════════════════════════════
# 🏠 ホームタブ
# ════════════════════════════════════════════
with tab_home:
    df = st.session_state.df_main
    wdf = st.session_state.df_weekly

    if df is None:
        st.info("データを読み込み中です...")
    else:
        # サマリ
        valid = df["前日差枚"].dropna()
        c1, c2, c3 = st.columns(3)
        c1.metric("総台数", f"{len(df)}台")
        c2.metric("プラス台", f"{(valid > 0).sum()}台")
        c3.metric("平均差枚", diff_sign(valid.mean()) if len(valid) > 0 else "-")

        # クイックフィルタ
        st.markdown('<div class="section-title">クイックフィルタ</div>', unsafe_allow_html=True)
        filters = ["全台", "前日凹み", "前日プラス", "ジャグラー", "⭐星印"]
        fcols = st.columns(len(filters))
        for i, f in enumerate(filters):
            if fcols[i].button(f, key=f"qf_{f}"):
                st.session_state.active_filter = f

        af = st.session_state.active_filter
        st.markdown(f'<div style="font-size:0.7rem;color:#7a8aaa;margin-bottom:0.6rem;">フィルタ: <span style="color:#00ffcc;">{af}</span></div>', unsafe_allow_html=True)

        df_sorted = df.dropna(subset=["前日差枚"]).sort_values("前日差枚", ascending=False)
        if af == "前日凹み":
            df_sorted = df_sorted[df_sorted["前日差枚"] < 0].sort_values("前日差枚")
        elif af == "前日プラス":
            df_sorted = df_sorted[df_sorted["前日差枚"] > 0]
        elif af == "ジャグラー":
            df_sorted = df_sorted[df_sorted["is_juggler"]]
        elif af == "⭐星印":
            starred = [k for k, v in st.session_state.stars.items() if v]
            df_sorted = df_sorted[df_sorted["台番"].apply(lambda x: str(int(x)) if not np.isnan(x) else "").isin(starred)]

        # おすすめカード（上位3 + 凹み狙い2）
        st.markdown('<div class="section-title">⭐ おすすめ台</div>', unsafe_allow_html=True)
        top3 = df.nlargest(3, "前日差枚")
        bot2 = df.nsmallest(2, "前日差枚")
        card_df = pd.concat([top3, bot2]).drop_duplicates()

        for idx, row in card_df.iterrows():
            diff = row["前日差枚"]
            score = row["スコア"]
            sc = score_color(score)
            dc = diff_class(diff)
            week_avg = row.get("週平均", diff)
            is_hot = diff > 0 if not np.isnan(diff) else True
            card_class = "card-hot" if is_hot else "card-cold"
            台番_str = str(int(row["台番"])) if not np.isnan(row["台番"]) else "?"
            is_starred = st.session_state.stars.get(台番_str, False)
            star_icon = "⭐" if is_starred else "☆"

            badges = ""
            if not np.isnan(diff):
                if diff > 2000: badges += '<span class="badge badge-hot">🔥 好調</span>'
                elif diff < -2000: badges += '<span class="badge badge-cold">❄ 凹み狙い</span>'
            if is_starred: badges += '<span class="badge badge-star">⭐ 注目</span>'
            if row["is_juggler"]: badges += '<span class="badge badge-juggler">🎰 ジャグ</span>'

            st.markdown(f"""
            <div class="card {card_class}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div style="flex:1;">
                  <div class="machine-num">台番 {台番_str}</div>
                  <div class="machine-name">{row['機種名']}</div>
                  <div>{badges}</div>
                </div>
                <div style="text-align:right;">
                  <div class="{dc}">{diff_sign(diff)}</div>
                  <div style="font-size:0.65rem;color:#7a8aaa;">週平均 {diff_sign(week_avg)}</div>
                </div>
              </div>
              <div style="margin-top:6px;">
                <div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#7a8aaa;margin-bottom:2px;">
                  <span>スコア</span><span style="color:{sc};">{score:.0f}/100</span>
                </div>
                <div class="score-bar-wrap">
                  <div class="score-bar-fill" style="width:{score}%;background:linear-gradient(90deg,{sc}88,{sc});"></div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # スパークライン
            if wdf is not None and not wdf.empty and idx in wdf.index:
                vals = wdf.loc[idx].dropna().values.tolist()
                if vals:
                    color = "#00ff88" if is_hot else "#ff4444"
                    fig = go.Figure(go.Scatter(
                        x=list(range(len(vals))), y=vals,
                        mode="lines", line=dict(color=color, width=2),
                        fill="tozeroy", fillcolor=color + "1a",
                    ))
                    fig.update_layout(
                        height=45, margin=dict(l=0,r=0,t=0,b=0),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(visible=False), yaxis=dict(visible=False),
                        showlegend=False,
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"spark_home_{idx}")

            # 星・メモボタン
            btn_c1, btn_c2 = st.columns([1, 3])
            with btn_c1:
                if st.button(f"{star_icon} 星", key=f"star_home_{idx}"):
                    st.session_state.stars[台番_str] = not is_starred
                    st.rerun()
            with btn_c2:
                memo = st.session_state.memos.get(台番_str, "")
                if memo:
                    st.markdown(f'<div class="memo-box">📝 {memo}</div>', unsafe_allow_html=True)

        # ランキング
        st.markdown('<div class="section-title">📊 差枚ランキング</div>', unsafe_allow_html=True)
        c_top, c_bot = st.columns(2)
        with c_top:
            st.markdown('<div style="font-size:0.75rem;color:#00ff88;margin-bottom:4px;">▲ TOP 5</div>', unsafe_allow_html=True)
            top5 = df.nlargest(5, "前日差枚")[["台番", "機種名", "前日差枚"]].copy()
            top5["台番"] = top5["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            top5["前日差枚"] = top5["前日差枚"].apply(diff_sign)
            st.dataframe(top5, hide_index=True, use_container_width=True, height=210)
        with c_bot:
            st.markdown('<div style="font-size:0.75rem;color:#ff4444;margin-bottom:4px;">▼ WORST 5</div>', unsafe_allow_html=True)
            bot5 = df.nsmallest(5, "前日差枚")[["台番", "機種名", "前日差枚"]].copy()
            bot5["台番"] = bot5["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            bot5["前日差枚"] = bot5["前日差枚"].apply(diff_sign)
            st.dataframe(bot5, hide_index=True, use_container_width=True, height=210)

# ════════════════════════════════════════════
# 📈 トレンドタブ
# ════════════════════════════════════════════
with tab_trend:
    df = st.session_state.df_main
    wdf = st.session_state.df_weekly

    if df is None:
        st.info("データを読み込み中です...")
    elif wdf is None or wdf.empty:
        st.warning("週次データがありません。scraper.pyで週次データも取得されているか確認してください。")
    else:
        machine_options = df.apply(
            lambda r: f"#{int(r['台番']) if not np.isnan(r['台番']) else '?'} {r['機種名']}", axis=1
        ).tolist()

        selected = st.multiselect(
            "台を選択（最大6台）",
            options=machine_options,
            default=machine_options[:3] if len(machine_options) >= 3 else machine_options,
            max_selections=6,
        )

        if selected:
            sel_idx = [machine_options.index(l) for l in selected]
            df_sel = df.iloc[sel_idx]

            # トレンドグラフ
            st.markdown('<div class="section-title">1週間差枚トレンド</div>', unsafe_allow_html=True)
            colors = ["#00ffcc", "#00ff88", "#ff8844", "#aa88ff", "#ff4488", "#44aaff"]
            fig = go.Figure()

            for i, (idx, row) in enumerate(df_sel.iterrows()):
                if idx not in wdf.index: continue
                vals = wdf.loc[idx].dropna()
                if len(vals) == 0: continue
                color = colors[i % len(colors)]
                label = f"#{int(row['台番'])} {row['機種名']}"

                fig.add_trace(go.Scatter(
                    x=list(vals.index), y=vals.values,
                    mode="lines+markers", name=label,
                    line=dict(color=color, width=2.5),
                    marker=dict(size=6, color=color),
                ))
                if len(vals) >= 3:
                    ma = pd.Series(vals.values).rolling(3).mean()
                    fig.add_trace(go.Scatter(
                        x=list(vals.index), y=ma.values,
                        mode="lines", line=dict(color=color, width=1, dash="dot"),
                        opacity=0.5, showlegend=False,
                    ))

            fig.add_hline(y=0, line_dash="dash", line_color="#ffffff22")
            fig.update_layout(
                height=320, paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1520",
                font=dict(family="Noto Sans JP", color="#a0b0cc", size=11),
                legend=dict(bgcolor="#111828", bordercolor="#1e2d45", borderwidth=1,
                           font=dict(size=10), orientation="h", y=-0.25),
                xaxis=dict(showgrid=True, gridcolor="#1e2d45"),
                yaxis=dict(showgrid=True, gridcolor="#1e2d45", title="差枚数"),
                margin=dict(l=50, r=10, t=20, b=70),
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # スコアゲージ
            st.markdown('<div class="section-title">期待値スコア</div>', unsafe_allow_html=True)
            for idx, row in df_sel.iterrows():
                score = row["スコア"]
                sc = score_color(score)
                name = f"#{int(row['台番']) if not np.isnan(row['台番']) else '?'} {row['機種名']}"
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=score,
                    title=dict(text=name, font=dict(size=11, color="#a0b0cc")),
                    number=dict(font=dict(size=22, family="Orbitron", color=sc)),
                    gauge=dict(
                        axis=dict(range=[0, 100], tickfont=dict(size=9)),
                        bar=dict(color=sc, thickness=0.25),
                        bgcolor="#0d1520", bordercolor="#1e2d45",
                        steps=[
                            dict(range=[0, 40], color="#ff444422"),
                            dict(range=[40, 65], color="#ffcc0022"),
                            dict(range=[65, 100], color="#00ff8822"),
                        ],
                    )
                ))
                fig_g.update_layout(
                    height=180, margin=dict(l=20,r=20,t=40,b=10),
                    paper_bgcolor="#0a0e1a", font_color="#a0b0cc",
                )
                st.plotly_chart(fig_g, use_container_width=True,
                               config={"displayModeBar": False}, key=f"gauge_{idx}")

# ════════════════════════════════════════════
# 📋 全台一覧タブ
# ════════════════════════════════════════════
with tab_all:
    df = st.session_state.df_main

    if df is None:
        st.info("データを読み込み中です...")
    else:
        # フィルタ
        machine_types = ["全機種"] + sorted(df["機種名"].unique().tolist())
        sel_m = st.selectbox("機種名", machine_types)
        c1, c2 = st.columns(2)
        min_d = c1.number_input("差枚 下限", value=-9999, step=500)
        max_d = c2.number_input("差枚 上限", value=9999, step=500)
        sort_by = st.selectbox("ソート", ["前日差枚", "スコア", "週平均", "台番"])
        asc = st.checkbox("昇順", value=False)

        df_v = df.copy()
        if sel_m != "全機種":
            df_v = df_v[df_v["機種名"] == sel_m]
        df_v = df_v[df_v["前日差枚"].between(min_d, max_d, inclusive="both")]
        sort_col_map = {"前日差枚": "前日差枚", "スコア": "スコア", "週平均": "週平均", "台番": "台番"}
        df_v = df_v.sort_values(sort_col_map[sort_by], ascending=asc, na_position="last")

        st.markdown(f'<div style="font-size:0.75rem;color:#7a8aaa;margin:0.3rem 0;">{len(df_v)} 台表示中</div>', unsafe_allow_html=True)

        disp = df_v[["台番", "機種名", "前日差枚", "週平均", "スコア", "回転数"]].copy()
        disp["台番"] = disp["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
        disp["前日差枚"] = disp["前日差枚"].apply(diff_sign)
        disp["週平均"] = disp["週平均"].apply(diff_sign)
        disp["スコア"] = disp["スコア"].apply(lambda x: f"{x:.0f}")
        disp["回転数"] = disp["回転数"].apply(lambda x: f"{int(x):,}" if not np.isnan(x) else "-")
        st.dataframe(disp, hide_index=True, use_container_width=True, height=400)

        # 分布グラフ
        st.markdown('<div class="section-title">差枚分布</div>', unsafe_allow_html=True)
        vals = df_v["前日差枚"].dropna()
        if len(vals) > 0:
            fig_h = go.Figure(go.Histogram(
                x=vals, nbinsx=20,
                marker_color=["#00ff88" if v >= 0 else "#ff4444" for v in vals],
                opacity=0.8,
            ))
            fig_h.add_vline(x=0, line_dash="dash", line_color="#ffffff44")
            fig_h.update_layout(
                height=180, paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1520",
                margin=dict(l=40,r=10,t=10,b=30),
                xaxis=dict(gridcolor="#1e2d45", tickfont=dict(size=9, color="#7a8aaa")),
                yaxis=dict(gridcolor="#1e2d45", tickfont=dict(size=9, color="#7a8aaa")),
                showlegend=False, bargap=0.1,
            )
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

# ════════════════════════════════════════════
# ⭐ メモタブ
# ════════════════════════════════════════════
with tab_memo:
    df = st.session_state.df_main

    if df is None:
        st.info("データを読み込み中です...")
    else:
        st.markdown('<div class="section-title">台ごとのメモ・星印</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.75rem;color:#7a8aaa;margin-bottom:0.8rem;">星印をつけた台・メモを管理できます</div>', unsafe_allow_html=True)

        # 台番選択
        machine_options = df.apply(
            lambda r: f"#{int(r['台番']) if not np.isnan(r['台番']) else '?'} {r['機種名']}", axis=1
        ).tolist()
        sel_machine = st.selectbox("台を選択", machine_options)
        sel_idx = machine_options.index(sel_machine)
        row = df.iloc[sel_idx]
        台番_str = str(int(row["台番"])) if not np.isnan(row["台番"]) else "?"

        # 星印
        is_starred = st.session_state.stars.get(台番_str, False)
        star_label = "⭐ 星印ON（タップでOFF）" if is_starred else "☆ 星印OFF（タップでON）"
        if st.button(star_label, use_container_width=True):
            st.session_state.stars[台番_str] = not is_starred
            st.rerun()

        # メモ入力
        memo_key = f"memo_input_{台番_str}"
        current_memo = st.session_state.memos.get(台番_str, "")
        new_memo = st.text_area(
            "メモ（設定変更・挙動など自由に）",
            value=current_memo,
            height=100,
            placeholder="例：右側のランプが赤く光りやすい、高設定か？",
            key=memo_key,
        )
        if st.button("💾 メモを保存", use_container_width=True):
            st.session_state.memos[台番_str] = new_memo
            st.success("保存しました")

        # 星印・メモ一覧
        st.markdown('<div class="section-title">星印一覧</div>', unsafe_allow_html=True)
        starred_list = [(k, v) for k, v in st.session_state.stars.items() if v]
        if starred_list:
            for 台番_s, _ in starred_list:
                memo = st.session_state.memos.get(台番_s, "")
                # dfから機種名を探す
                matched = df[df["台番"].apply(lambda x: str(int(x)) if not np.isnan(x) else "") == 台番_s]
                機種 = matched.iloc[0]["機種名"] if len(matched) > 0 else "?"
                diff = matched.iloc[0]["前日差枚"] if len(matched) > 0 else np.nan
                dc = diff_class(diff)
                st.markdown(f"""
                <div class="card">
                  <div style="display:flex;justify-content:space-between;">
                    <div>
                      <div class="machine-num">⭐ 台番 {台番_s}</div>
                      <div class="machine-name">{機種}</div>
                    </div>
                    <div class="{dc}">{diff_sign(diff)}</div>
                  </div>
                  {'<div class="memo-box">📝 ' + memo + '</div>' if memo else ''}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#7a8aaa;font-size:0.8rem;">星印をつけた台はまだありません</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# フッター
# ─────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:1.5rem 0 0.5rem;font-size:0.65rem;color:#3a4a5a;">
  SLOTDASH v2 &nbsp;|&nbsp; スーパーコスモ堺専用 &nbsp;|&nbsp; 個人利用専用<br>
  ※ このアプリはギャンブルを推奨するものではありません
</div>
""", unsafe_allow_html=True)
