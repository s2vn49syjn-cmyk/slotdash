"""
パチスロ台選びダッシュボード - みんレポ差枚レポート対応
Mobile-first / Dark mode / Plotly対応
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
import json
import re
from datetime import datetime, date
import base64

# ─────────────────────────────────────────────
# ページ設定（最初に呼ぶ）
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="スロダッシュ | 台選びナビ",
    page_icon="🎰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# グローバルCSS（ネオン調ダークテーマ）
# ─────────────────────────────────────────────
DARK_CSS = """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+JP:wght@300;400;700&display=swap');

/* ── ベースリセット ── */
html, body, [class*="css"] {
    background-color: #0a0e1a !important;
    color: #e0e6f0 !important;
    font-family: 'Noto Sans JP', sans-serif !important;
}

/* ── メインコンテナ ── */
.main .block-container {
    padding: 0.5rem 1rem 2rem 1rem !important;
    max-width: 480px !important;
    margin: auto !important;
}

/* ── ヘッダータイトル ── */
.neon-title {
    font-family: 'Orbitron', monospace;
    font-size: 1.6rem;
    font-weight: 900;
    color: #00ffcc;
    text-shadow: 0 0 10px #00ffcc88, 0 0 30px #00ffcc44;
    letter-spacing: 2px;
    margin: 0;
    line-height: 1.1;
}
.neon-sub {
    font-size: 0.72rem;
    color: #7a8aaa;
    letter-spacing: 1px;
    margin-top: 2px;
}

/* ── ヘッダーバー ── */
.header-bar {
    background: linear-gradient(135deg, #0f1729 0%, #141c30 100%);
    border-bottom: 1px solid #00ffcc33;
    padding: 0.8rem 1rem;
    margin: -0.5rem -1rem 1rem -1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 4px 20px #00ffcc11;
}

/* ── カード共通 ── */
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

/* ── 台番 ── */
.machine-num {
    font-family: 'Orbitron', monospace;
    font-size: 0.7rem;
    color: #7a8aaa;
    letter-spacing: 1px;
}
.machine-name {
    font-size: 1rem;
    font-weight: 700;
    color: #c8d8f0;
    margin: 2px 0 6px;
}

/* ── 差枚数値 ── */
.diff-plus {
    font-family: 'Orbitron', monospace;
    font-size: 1.6rem;
    font-weight: 900;
    color: #00ff88;
    text-shadow: 0 0 8px #00ff8866;
}
.diff-minus {
    font-family: 'Orbitron', monospace;
    font-size: 1.6rem;
    font-weight: 900;
    color: #ff4444;
    text-shadow: 0 0 8px #ff444466;
}
.diff-neutral {
    font-family: 'Orbitron', monospace;
    font-size: 1.6rem;
    font-weight: 900;
    color: #ffcc00;
    text-shadow: 0 0 8px #ffcc0066;
}

/* ── スコアバー ── */
.score-bar-wrap {
    background: #0a0e1a;
    border-radius: 6px;
    height: 6px;
    margin-top: 6px;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 0.5s;
}

/* ── バッジ ── */
.badge {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    margin-right: 4px;
    letter-spacing: 0.5px;
}
.badge-hot { background: #00ff8822; color: #00ff88; border: 1px solid #00ff8844; }
.badge-cold { background: #ff444422; color: #ff6666; border: 1px solid #ff444444; }
.badge-warn { background: #ffcc0022; color: #ffcc00; border: 1px solid #ffcc0044; }
.badge-juggler { background: #8844ff22; color: #aa88ff; border: 1px solid #8844ff44; }

/* ── セクションタイトル ── */
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

/* ── フィルタボタン群 ── */
div[data-testid="stHorizontalBlock"] > div {
    flex: 1 1 auto !important;
}

/* ── Streamlit ボタン上書き ── */
.stButton > button {
    background: #111828 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 8px !important;
    color: #a0b0cc !important;
    font-size: 0.75rem !important;
    padding: 0.4rem 0.5rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    border-color: #00ffcc66 !important;
    color: #00ffcc !important;
    box-shadow: 0 0 10px #00ffcc22 !important;
}
.stButton > button:active { transform: scale(0.97) !important; }

/* ── テーブル ── */
.stDataFrame { border-radius: 8px; overflow: hidden; }
.stDataFrame table { background: #0d1520 !important; }

/* ── テキスト入力 ── */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background-color: #111828 !important;
    border: 1px solid #1e2d45 !important;
    color: #e0e6f0 !important;
    border-radius: 8px !important;
}

/* ── ファイルアップロード ── */
.stFileUploader {
    border: 1px dashed #1e2d45 !important;
    border-radius: 10px !important;
    background: #0d1520 !important;
}

/* ── タブ ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0d1520 !important;
    border-radius: 10px !important;
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: #7a8aaa !important;
    font-size: 0.8rem !important;
    padding: 0.4rem 0.8rem !important;
}
.stTabs [aria-selected="true"] {
    background: #1e2d45 !important;
    color: #00ffcc !important;
}

/* ── expander ── */
.streamlit-expanderHeader {
    background: #111828 !important;
    border-radius: 8px !important;
    color: #a0b0cc !important;
}

/* ── scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #1e2d45; border-radius: 2px; }

/* ── metric ── */
[data-testid="stMetric"] {
    background: #111828;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    padding: 0.6rem 0.8rem;
}
[data-testid="stMetricLabel"] { font-size: 0.7rem !important; color: #7a8aaa !important; }
[data-testid="stMetricValue"] { font-family: 'Orbitron', monospace !important; font-size: 1.1rem !important; }

/* ── ランキング行色 ── */
.rank-plus { background-color: #00ff8811 !important; }
.rank-minus { background-color: #ff444411 !important; }
</style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# サンプルCSVデータ
# ─────────────────────────────────────────────
SAMPLE_CSV = """台番,機種名,前日差枚,前日回転数,前日ボーナス数,7日前差枚,6日前差枚,5日前差枚,4日前差枚,3日前差枚,2日前差枚,前日差枚2
101,マイジャグラー5,+2340,600,18,-800,+1200,+2100,-300,+1800,+900,+2340
102,マイジャグラー5,-1580,550,12,+2000,-500,-1200,+800,-1800,-900,-1580
103,ハッピージャグラー3,+890,480,15,-200,+400,+1100,-600,+300,+500,+890
104,アイムジャグラー7,-2100,620,10,+1500,+2000,-800,-1500,-2000,-1800,-2100
105,ゴーゴージャグラー3,+3200,700,22,-1000,+500,+2800,+1200,+2500,+3000,+3200
106,北斗の拳 新伝説,-4500,800,8,+3000,+2500,-1000,-3000,-4000,-5000,-4500
107,バジリスク絆2,+1200,500,14,+800,-200,+600,+1800,+1200,+900,+1200
108,Re:ゼロから始める,-980,450,11,-500,-800,-1200,+200,-1000,-800,-980
109,スマスロ北斗,-3200,750,9,+2000,-500,-2000,-1000,-2500,-3000,-3200
110,Lエヴァンゲリオン,+560,420,16,-1200,+300,+800,-400,+600,+300,+560
111,ファンキージャグラー3,+1800,580,20,+400,+800,+1500,+900,+1200,+1600,+1800
112,クレアの秘宝伝,-1100,390,13,-300,-600,-900,-200,-800,-1000,-1100
113,スターウォーズ,+2800,650,19,+1000,+1500,+2000,+800,+2200,+2600,+2800
114,Lまどかマギカ,-500,410,12,+200,-100,-300,+100,-400,-600,-500
115,Lバジリスク絆3,+4100,720,25,-500,+800,+2000,+1500,+3000,+3800,+4100
"""

# ─────────────────────────────────────────────
# ホールプリセット
# ─────────────────────────────────────────────
HALL_PRESETS = [
    "手動入力",
    "マルハン（泉大津）",
    "マルハン（堺）",
    "ガイア（岸和田）",
    "123（難波）",
    "ニラク（和泉）",
    "スロット専門店A",
]

# ジャグラー系機種キーワード
JUGGLER_KEYWORDS = ["ジャグラー", "juggler", "JUGGLER"]

# ─────────────────────────────────────────────
# ユーティリティ関数
# ─────────────────────────────────────────────

def parse_number(val):
    """文字列数値（+2340, -1580など）をfloatに変換"""
    if pd.isna(val):
        return np.nan
    s = str(val).strip().replace(",", "").replace("＋", "+").replace("－", "-").replace("ー", "-")
    # 符号付き数値抽出
    m = re.search(r"[+-]?\d+", s)
    return float(m.group()) if m else np.nan

def detect_columns(df: pd.DataFrame) -> dict:
    """列名を自動認識してマッピングを返す"""
    col_map = {}
    cols_lower = {c.lower().replace(" ", "").replace("　", ""): c for c in df.columns}

    # 台番
    for key in ["台番", "台no", "台number", "machine_no", "no", "番号"]:
        if key in cols_lower:
            col_map["台番"] = cols_lower[key]; break

    # 機種名
    for key in ["機種名", "機種", "machinename", "name", "機械名"]:
        if key in cols_lower:
            col_map["機種名"] = cols_lower[key]; break

    # 前日差枚
    for key in ["前日差枚", "差枚", "前日差枚2", "yesterday_diff", "diff"]:
        if key in cols_lower:
            col_map["前日差枚"] = cols_lower[key]; break

    # 前日回転数
    for key in ["前日回転数", "回転数", "games", "g数", "ゲーム数"]:
        if key in cols_lower:
            col_map["回転数"] = cols_lower[key]; break

    # 前日ボーナス
    for key in ["前日ボーナス数", "ボーナス数", "bonus", "bb+rb", "ボーナス"]:
        if key in cols_lower:
            col_map["ボーナス"] = cols_lower[key]; break

    return col_map

def extract_weekly_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    1週間分の日別差枚を抽出する。
    - 「7日前差枚」「6日前差枚」...「前日差枚」のような列
    - または差枚リスト列
    """
    week_cols = []
    day_labels = []

    # パターン1: N日前差枚 という列
    day_pattern = re.compile(r"(\d+)日前差枚|前日差枚$|前々日差枚")
    date_cols_found = []
    for col in df.columns:
        stripped = col.strip()
        m = re.search(r"(\d+)日前", stripped)
        if m:
            days_ago = int(m.group(1))
            date_cols_found.append((days_ago, col))
        elif "前日差枚" in stripped and "2" not in stripped:
            date_cols_found.append((1, col))

    if date_cols_found:
        date_cols_found.sort(key=lambda x: x[0], reverse=True)
        labels_map = {d: f"-{d}日" for d, _ in date_cols_found}
        labels_map[1] = "前日"
        week_cols = [c for _, c in date_cols_found]
        day_labels = [labels_map[d] for d, _ in date_cols_found]

    if week_cols:
        weekly = df[week_cols].copy()
        weekly.columns = day_labels
        for col in weekly.columns:
            weekly[col] = weekly[col].apply(parse_number)
        return weekly

    return pd.DataFrame()

def calc_score(row, weekly_df=None, idx=None) -> float:
    """
    狙い目スコア計算 (0-100)
    = (前日差枚 / 1000) * 30 + (週平均 / 500) * 40 + トレンドボーナス * 30
    """
    score = 50.0  # 基準点

    # 前日差枚による加点（-30〜+30）
    diff = row.get("前日差枚_num", 0) or 0
    score += np.clip(diff / 1000 * 30, -30, 30)

    # 週平均による加点（-20〜+20）
    if weekly_df is not None and idx is not None and idx in weekly_df.index:
        week_vals = weekly_df.loc[idx].dropna().values
        if len(week_vals) > 0:
            avg = np.mean(week_vals)
            score += np.clip(avg / 500 * 20, -20, 20)

    # トレンドボーナス（直近3日で上昇傾向なら+10）
    if weekly_df is not None and idx is not None and idx in weekly_df.index:
        week_vals = weekly_df.loc[idx].dropna().values
        if len(week_vals) >= 3:
            recent = week_vals[-3:]
            if recent[-1] > recent[0]:
                score += 10
            elif recent[-1] < recent[0]:
                score -= 10

    return float(np.clip(score, 0, 100))

def score_color(score: float) -> str:
    if score >= 70: return "#00ff88"
    if score >= 50: return "#ffcc00"
    return "#ff4444"

def diff_class(val: float) -> str:
    if val > 0: return "diff-plus"
    if val < 0: return "diff-minus"
    return "diff-neutral"

def diff_sign(val: float) -> str:
    return f"+{int(val):,}" if val >= 0 else f"{int(val):,}"

def is_juggler(name: str) -> bool:
    return any(k in name for k in JUGGLER_KEYWORDS)

def make_sparkline(values: list, color: str = "#00ffcc") -> go.Figure:
    """ミニ折れ線グラフ（カード内用）"""
    fig = go.Figure()
    x = list(range(len(values)))
    fig.add_trace(go.Scatter(
        x=x, y=values,
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=color.replace(")", ",0.1)").replace("rgb", "rgba") if "rgb" in color else color + "1a",
    ))
    fig.update_layout(
        height=50, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig

def make_trend_chart(df_filtered: pd.DataFrame, weekly_df: pd.DataFrame) -> go.Figure:
    """トレンド詳細：複数台重ねグラフ"""
    fig = go.Figure()
    colors = ["#00ffcc", "#00ff88", "#ff8844", "#aa88ff", "#ff4488", "#44aaff"]

    for i, (idx, row) in enumerate(df_filtered.iterrows()):
        if idx not in weekly_df.index:
            continue
        vals = weekly_df.loc[idx].dropna()
        if len(vals) == 0:
            continue
        name_label = f"#{int(row['台番'])} {row['機種名']}"
        color = colors[i % len(colors)]

        fig.add_trace(go.Scatter(
            x=list(vals.index),
            y=vals.values,
            mode="lines+markers",
            name=name_label,
            line=dict(color=color, width=2.5),
            marker=dict(size=6, color=color),
        ))

        # 移動平均（3点）
        if len(vals) >= 3:
            ma = pd.Series(vals.values).rolling(3).mean()
            fig.add_trace(go.Scatter(
                x=list(vals.index),
                y=ma.values,
                mode="lines",
                name=f"{name_label} MA",
                line=dict(color=color, width=1, dash="dot"),
                opacity=0.5,
                showlegend=False,
            ))

    fig.add_hline(y=0, line_dash="dash", line_color="#ffffff22", line_width=1)
    fig.update_layout(
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0d1520",
        font=dict(family="Noto Sans JP", color="#a0b0cc", size=11),
        legend=dict(
            bgcolor="#111828", bordercolor="#1e2d45", borderwidth=1,
            font=dict(size=10), orientation="h", y=-0.2,
        ),
        xaxis=dict(
            showgrid=True, gridcolor="#1e2d45", gridwidth=1,
            title="",
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#1e2d45", gridwidth=1,
            title="差枚数",
            tickfont=dict(size=10),
            zeroline=False,
        ),
        margin=dict(l=50, r=10, t=20, b=60),
        height=320,
        hovermode="x unified",
    )
    return fig

# ─────────────────────────────────────────────
# セッションステート初期化
# ─────────────────────────────────────────────
if "df_main" not in st.session_state:
    st.session_state.df_main = None
if "df_weekly" not in st.session_state:
    st.session_state.df_weekly = None
if "hall_name" not in st.session_state:
    st.session_state.hall_name = ""
if "selected_machines" not in st.session_state:
    st.session_state.selected_machines = []
if "active_filter" not in st.session_state:
    st.session_state.active_filter = "全台"

# ─────────────────────────────────────────────
# データ読み込み・前処理
# ─────────────────────────────────────────────
def load_data(source, source_type="csv") -> bool:
    """CSVまたはテキストからDataFrameを構築してセッションに保存"""
    try:
        if source_type == "csv":
            df = pd.read_csv(source, encoding="utf-8-sig")
        else:  # text paste
            lines = [l.strip() for l in source.strip().split("\n") if l.strip()]
            # タブ or カンマ区切り自動判定
            sep = "\t" if "\t" in lines[0] else ","
            content = "\n".join(lines)
            df = pd.read_csv(io.StringIO(content), sep=sep)

        col_map = detect_columns(df)

        # 必須列チェック
        if "台番" not in col_map or "機種名" not in col_map:
            st.error("⚠️ 台番・機種名の列が見つかりませんでした。列名を確認してください。")
            return False

        # 数値変換
        df_proc = pd.DataFrame()
        df_proc["台番"] = df[col_map["台番"]].apply(parse_number)
        df_proc["機種名"] = df[col_map["機種名"]].astype(str).str.strip()

        if "前日差枚" in col_map:
            df_proc["前日差枚_num"] = df[col_map["前日差枚"]].apply(parse_number)
        else:
            df_proc["前日差枚_num"] = np.nan

        if "回転数" in col_map:
            df_proc["回転数"] = df[col_map["回転数"]].apply(parse_number)
        else:
            df_proc["回転数"] = np.nan

        if "ボーナス" in col_map:
            df_proc["ボーナス"] = df[col_map["ボーナス"]].apply(parse_number)
        else:
            df_proc["ボーナス"] = np.nan

        df_proc.index = df.index

        # 週次データ抽出
        weekly_df = extract_weekly_data(df)
        df_proc.index = range(len(df_proc))
        if not weekly_df.empty:
            weekly_df.index = range(len(weekly_df))

        # 週平均
        if not weekly_df.empty:
            df_proc["週平均差枚"] = weekly_df.mean(axis=1)
        else:
            df_proc["週平均差枚"] = df_proc["前日差枚_num"]

        # スコア計算
        df_proc["スコア"] = [
            calc_score(row, weekly_df if not weekly_df.empty else None, idx)
            for idx, row in df_proc.iterrows()
        ]

        # ジャグラーフラグ
        df_proc["is_juggler"] = df_proc["機種名"].apply(is_juggler)

        st.session_state.df_main = df_proc
        st.session_state.df_weekly = weekly_df if not weekly_df.empty else pd.DataFrame()
        return True

    except Exception as e:
        st.error(f"❌ データ読み込みエラー: {e}")
        return False

# ─────────────────────────────────────────────
# ── UI: ヘッダー ──
# ─────────────────────────────────────────────
today_str = datetime.now().strftime("%Y年%-m月%-d日")

st.markdown(f"""
<div class="header-bar">
  <div>
    <div class="neon-title">🎰 SLOTDASH</div>
    <div class="neon-sub">{today_str} &nbsp;|&nbsp; 台選びナビ</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ── タブ構成 ──
# ─────────────────────────────────────────────
tab_home, tab_trend, tab_all, tab_data = st.tabs(["🏠 ホーム", "📈 トレンド", "📋 全台", "📂 データ"])

# ════════════════════════════════════════════
# 📂 データタブ（先に定義してどのタブでもロード可）
# ════════════════════════════════════════════
with tab_data:
    st.markdown('<div class="section-title">ホール設定</div>', unsafe_allow_html=True)

    preset = st.selectbox("ホールプリセット", HALL_PRESETS, key="preset_select")
    if preset != "手動入力":
        st.session_state.hall_name = preset
    hall_input = st.text_input("ホール名（手動入力）", value=st.session_state.hall_name, key="hall_input")
    if hall_input:
        st.session_state.hall_name = hall_input

    st.markdown('<div class="section-title">データアップロード</div>', unsafe_allow_html=True)

    # サンプルCSVダウンロード
    sample_bytes = SAMPLE_CSV.encode("utf-8-sig")
    b64 = base64.b64encode(sample_bytes).decode()
    st.markdown(
        f'<a href="data:text/csv;base64,{b64}" download="sample_slot_data.csv" '
        f'style="color:#00ffcc;font-size:0.8rem;">⬇ サンプルCSVをダウンロード</a>',
        unsafe_allow_html=True
    )

    upload_method = st.radio("入力方法", ["📁 CSVアップロード", "📋 テキスト貼り付け"], horizontal=True)

    if upload_method == "📁 CSVアップロード":
        uploaded = st.file_uploader("CSVファイルを選択", type=["csv", "tsv", "txt"], label_visibility="collapsed")
        if uploaded is not None:
            if load_data(uploaded, "csv"):
                st.success(f"✅ {len(st.session_state.df_main)} 台のデータを読み込みました")
    else:
        pasted = st.text_area(
            "データをここに貼り付け（カンマ区切りまたはタブ区切り）",
            height=200,
            placeholder="台番,機種名,前日差枚,...\n101,マイジャグラー5,+2340,...",
        )
        if st.button("📊 データを解析", use_container_width=True):
            if pasted.strip():
                if load_data(pasted, "text"):
                    st.success(f"✅ {len(st.session_state.df_main)} 台を読み込みました")
            else:
                st.warning("データが空です")

    # サンプルデータ読み込み
    st.markdown("---")
    if st.button("🎲 サンプルデータで試す", use_container_width=True):
        if load_data(io.StringIO(SAMPLE_CSV), "csv"):
            st.session_state.hall_name = "サンプルホール（大阪）"
            st.success("✅ サンプルデータを読み込みました")
            st.rerun()

    # 現在のデータ概要
    if st.session_state.df_main is not None:
        df = st.session_state.df_main
        st.markdown('<div class="section-title">データ概要</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("総台数", f"{len(df)}台")
        valid_diff = df["前日差枚_num"].dropna()
        c2.metric("プラス台", f"{(valid_diff > 0).sum()}台")
        c3.metric("マイナス台", f"{(valid_diff < 0).sum()}台")

        st.markdown('<div class="section-title">週次データ</div>', unsafe_allow_html=True)
        wdf = st.session_state.df_weekly
        if not wdf.empty:
            st.info(f"📅 {len(wdf.columns)}日分の週次データを検出しました: {', '.join(wdf.columns)}")
        else:
            st.warning("週次データ（N日前差枚）の列が見つかりませんでした")

# ════════════════════════════════════════════
# 🏠 ホームタブ
# ════════════════════════════════════════════
with tab_home:
    df = st.session_state.df_main
    wdf = st.session_state.df_weekly

    if df is None:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem;">
          <div style="font-size:3rem;">🎰</div>
          <div style="color:#00ffcc;font-family:'Orbitron',monospace;font-size:1rem;margin:0.5rem 0;">データを読み込んでください</div>
          <div style="color:#7a8aaa;font-size:0.8rem;">「データ」タブからCSVをアップロード<br>またはテキストを貼り付け</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📂 データタブへ", use_container_width=True):
            st.info("上の「📂 データ」タブを選択してください")
    else:
        hall = st.session_state.hall_name or "未設定"
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem;">
          <div>
            <div style="font-size:0.7rem;color:#7a8aaa;">対象ホール</div>
            <div style="font-size:1rem;font-weight:700;color:#c8d8f0;">{hall}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:0.7rem;color:#7a8aaa;">総台数</div>
            <div style="font-family:'Orbitron',monospace;font-size:1rem;color:#00ffcc;">{len(df)}台</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── クイックフィルタ ──
        st.markdown('<div class="section-title">クイックフィルタ</div>', unsafe_allow_html=True)
        filters = ["全台", "前日凹み", "前日プラス", "ジャグラー系", "高スコア"]
        fcols = st.columns(len(filters))
        for i, f in enumerate(filters):
            if fcols[i].button(f, key=f"qf_{f}"):
                st.session_state.active_filter = f

        af = st.session_state.active_filter
        st.markdown(f'<div style="font-size:0.7rem;color:#7a8aaa;margin:-0.3rem 0 0.6rem;">▶ フィルタ中: <span style="color:#00ffcc;">{af}</span></div>', unsafe_allow_html=True)

        df_sorted = df.sort_values("前日差枚_num", ascending=False).dropna(subset=["前日差枚_num"])
        if af == "前日凹み":
            df_sorted = df_sorted[df_sorted["前日差枚_num"] < 0].sort_values("前日差枚_num")
        elif af == "前日プラス":
            df_sorted = df_sorted[df_sorted["前日差枚_num"] > 0]
        elif af == "ジャグラー系":
            df_sorted = df_sorted[df_sorted["is_juggler"]]
        elif af == "高スコア":
            df_sorted = df_sorted[df_sorted["スコア"] >= 65].sort_values("スコア", ascending=False)

        # ── おすすめカード ──
        st.markdown('<div class="section-title">⭐ おすすめ台</div>', unsafe_allow_html=True)

        # 前日プラス上位 + 凹み狙い目を混合
        top_cards = df.nlargest(3, "前日差枚_num")
        bottom_cards = df.nsmallest(2, "前日差枚_num")
        card_df = pd.concat([top_cards, bottom_cards]).drop_duplicates()

        for idx, row in card_df.iterrows():
            diff = row["前日差枚_num"]
            score = row["スコア"]
            sc = score_color(score)
            dc = diff_class(diff)
            week_avg = row.get("週平均差枚", diff)
            is_hot = diff > 0

            # バッジ
            badges = ""
            if diff > 2000: badges += '<span class="badge badge-hot">🔥 好調</span>'
            elif diff < -2000: badges += '<span class="badge badge-cold">❄ 凹み狙い</span>'
            if diff > 0 and week_avg < -500: badges += '<span class="badge badge-warn">⚠ 急上昇</span>'
            if row["is_juggler"]: badges += '<span class="badge badge-juggler">🎰 ジャグ</span>'

            card_class = "card-hot" if is_hot else "card-cold"

            # スパークライン用データ
            if not wdf.empty and idx in wdf.index:
                spark_vals = wdf.loc[idx].dropna().values.tolist()
                spark_color = "#00ff88" if is_hot else "#ff4444"
            else:
                spark_vals = []

            st.markdown(f"""
            <div class="card {card_class}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div style="flex:1;">
                  <div class="machine-num">台番 {int(row['台番']) if not np.isnan(row['台番']) else '?'}</div>
                  <div class="machine-name">{row['機種名']}</div>
                  <div>{badges}</div>
                </div>
                <div style="text-align:right;">
                  <div class="{dc}">{diff_sign(diff)}</div>
                  <div style="font-size:0.65rem;color:#7a8aaa;">週平均 {diff_sign(week_avg) if not np.isnan(week_avg) else '-'}</div>
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

            # スパークライン（Plotlyミニグラフ）
            if spark_vals:
                fig_spark = make_sparkline(spark_vals, spark_color)
                st.plotly_chart(fig_spark, use_container_width=True, config={"displayModeBar": False}, key=f"spark_{idx}")

        # ── ランキングテーブル ──
        st.markdown('<div class="section-title">📊 前日差枚ランキング</div>', unsafe_allow_html=True)

        col_top, col_bot = st.columns(2)
        with col_top:
            st.markdown('<div style="font-size:0.75rem;color:#00ff88;margin-bottom:4px;">▲ TOP 5</div>', unsafe_allow_html=True)
            top5 = df.nlargest(5, "前日差枚_num")[["台番", "機種名", "前日差枚_num"]].copy()
            top5.columns = ["台番", "機種名", "差枚"]
            top5["差枚"] = top5["差枚"].apply(lambda x: diff_sign(x) if not np.isnan(x) else "-")
            top5["台番"] = top5["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            st.dataframe(top5, hide_index=True, use_container_width=True, height=220)

        with col_bot:
            st.markdown('<div style="font-size:0.75rem;color:#ff4444;margin-bottom:4px;">▼ WORST 5</div>', unsafe_allow_html=True)
            bot5 = df.nsmallest(5, "前日差枚_num")[["台番", "機種名", "前日差枚_num"]].copy()
            bot5.columns = ["台番", "機種名", "差枚"]
            bot5["差枚"] = bot5["差枚"].apply(lambda x: diff_sign(x) if not np.isnan(x) else "-")
            bot5["台番"] = bot5["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            st.dataframe(bot5, hide_index=True, use_container_width=True, height=220)

        # ── サマリ指標 ──
        st.markdown('<div class="section-title">📈 本日のサマリ</div>', unsafe_allow_html=True)
        valid = df["前日差枚_num"].dropna()
        c1, c2, c3 = st.columns(3)
        best = valid.max()
        worst = valid.min()
        avg = valid.mean()
        c1.metric("最高差枚", diff_sign(best), delta=None)
        c2.metric("平均差枚", diff_sign(avg), delta=None)
        c3.metric("最低差枚", diff_sign(worst), delta=None)

# ════════════════════════════════════════════
# 📈 トレンドタブ
# ════════════════════════════════════════════
with tab_trend:
    df = st.session_state.df_main
    wdf = st.session_state.df_weekly

    if df is None:
        st.info("データタブからデータを読み込んでください")
    else:
        st.markdown('<div class="section-title">台選択（複数選択可）</div>', unsafe_allow_html=True)

        machine_options = df.apply(
            lambda r: f"#{int(r['台番']) if not np.isnan(r['台番']) else '?'} {r['機種名']}", axis=1
        ).tolist()

        selected_labels = st.multiselect(
            "表示する台を選択",
            options=machine_options,
            default=machine_options[:3] if len(machine_options) >= 3 else machine_options,
            max_selections=8,
            label_visibility="collapsed",
        )

        if selected_labels:
            selected_indices = [machine_options.index(l) for l in selected_labels]
            df_sel = df.iloc[selected_indices]

            if not wdf.empty:
                st.markdown('<div class="section-title">1週間差枚トレンド</div>', unsafe_allow_html=True)
                fig_trend = make_trend_chart(df_sel, wdf)
                st.plotly_chart(fig_trend, use_container_width=True, config={
                    "displayModeBar": True,
                    "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d", "autoScale2d"],
                    "displaylogo": False,
                })

                # 日別テーブル
                st.markdown('<div class="section-title">日別データ</div>', unsafe_allow_html=True)
                for idx, row in df_sel.iterrows():
                    if idx not in wdf.index:
                        continue
                    week_row = wdf.loc[idx]
                    label = f"#{int(row['台番']) if not np.isnan(row['台番']) else '?'} {row['機種名']}"
                    with st.expander(label, expanded=False):
                        detail = week_row.dropna().reset_index()
                        detail.columns = ["日付", "差枚"]
                        detail["差枚"] = detail["差枚"].apply(lambda x: diff_sign(x))
                        st.dataframe(detail, hide_index=True, use_container_width=True)
            else:
                st.warning("週次データがないためトレンドグラフを表示できません")

        # 期待値スコアゲージ
        st.markdown('<div class="section-title">期待値スコア</div>', unsafe_allow_html=True)
        if selected_labels:
            for idx, row in df_sel.iterrows():
                score = row["スコア"]
                sc = score_color(score)
                name = f"#{int(row['台番']) if not np.isnan(row['台番']) else '?'} {row['機種名']}"

                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=score,
                    title=dict(text=name, font=dict(size=11, color="#a0b0cc")),
                    number=dict(font=dict(size=24, family="Orbitron", color=sc)),
                    gauge=dict(
                        axis=dict(range=[0, 100], tickfont=dict(size=9, color="#7a8aaa")),
                        bar=dict(color=sc, thickness=0.25),
                        bgcolor="#0d1520",
                        bordercolor="#1e2d45",
                        steps=[
                            dict(range=[0, 40], color="#ff444422"),
                            dict(range=[40, 65], color="#ffcc0022"),
                            dict(range=[65, 100], color="#00ff8822"),
                        ],
                        threshold=dict(
                            line=dict(color=sc, width=2),
                            thickness=0.75,
                            value=score,
                        ),
                    )
                ))
                fig_gauge.update_layout(
                    height=180, margin=dict(l=20, r=20, t=40, b=10),
                    paper_bgcolor="#0a0e1a", font_color="#a0b0cc",
                )
                st.plotly_chart(fig_gauge, use_container_width=True,
                                config={"displayModeBar": False}, key=f"gauge_{idx}")

# ════════════════════════════════════════════
# 📋 全台一覧タブ
# ════════════════════════════════════════════
with tab_all:
    df = st.session_state.df_main
    wdf = st.session_state.df_weekly

    if df is None:
        st.info("データタブからデータを読み込んでください")
    else:
        st.markdown('<div class="section-title">フィルタ・ソート</div>', unsafe_allow_html=True)

        # 機種名フィルタ
        machine_types = ["全機種"] + sorted(df["機種名"].unique().tolist())
        sel_machine = st.selectbox("機種名フィルタ", machine_types)

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            min_diff = st.number_input("差枚 下限", value=-9999, step=500)
        with col_f2:
            max_diff = st.number_input("差枚 上限", value=9999, step=500)

        sort_col = st.selectbox("ソート列", ["前日差枚_num", "スコア", "週平均差枚", "台番", "回転数"])
        sort_asc = st.checkbox("昇順", value=False)

        # フィルタ適用
        df_view = df.copy()
        if sel_machine != "全機種":
            df_view = df_view[df_view["機種名"] == sel_machine]
        df_view = df_view[
            (df_view["前日差枚_num"] >= min_diff) & (df_view["前日差枚_num"] <= max_diff)
        ]
        df_view = df_view.sort_values(sort_col, ascending=sort_asc, na_position="last")

        st.markdown(f'<div style="font-size:0.75rem;color:#7a8aaa;margin:0.3rem 0;">{len(df_view)} 台表示中</div>', unsafe_allow_html=True)

        # 表示用テーブル整形
        display_df = df_view[["台番", "機種名", "前日差枚_num", "週平均差枚", "スコア", "回転数"]].copy()
        display_df.columns = ["台番", "機種名", "前日差枚", "週平均", "スコア", "回転数"]
        display_df["台番"] = display_df["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
        display_df["前日差枚"] = display_df["前日差枚"].apply(lambda x: diff_sign(x) if not np.isnan(x) else "-")
        display_df["週平均"] = display_df["週平均"].apply(lambda x: diff_sign(x) if not np.isnan(x) else "-")
        display_df["スコア"] = display_df["スコア"].apply(lambda x: f"{x:.0f}" if not np.isnan(x) else "-")
        display_df["回転数"] = display_df["回転数"].apply(lambda x: f"{int(x):,}" if not np.isnan(x) else "-")

        st.dataframe(display_df, hide_index=True, use_container_width=True, height=400)

        # ミニ差枚分布グラフ
        st.markdown('<div class="section-title">差枚分布</div>', unsafe_allow_html=True)
        valid_diffs = df_view["前日差枚_num"].dropna()
        if len(valid_diffs) > 0:
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=valid_diffs,
                nbinsx=20,
                marker_color=[
                    "#00ff88" if v >= 0 else "#ff4444"
                    for v in valid_diffs
                ],
                opacity=0.8,
            ))
            fig_hist.add_vline(x=0, line_dash="dash", line_color="#ffffff44", line_width=1)
            fig_hist.update_layout(
                height=200,
                paper_bgcolor="#0a0e1a",
                plot_bgcolor="#0d1520",
                margin=dict(l=40, r=10, t=10, b=30),
                xaxis=dict(title="差枚", gridcolor="#1e2d45", tickfont=dict(size=9, color="#7a8aaa")),
                yaxis=dict(title="台数", gridcolor="#1e2d45", tickfont=dict(size=9, color="#7a8aaa")),
                showlegend=False,
                bargap=0.1,
            )
            st.plotly_chart(fig_hist, use_container_width=True,
                            config={"displayModeBar": False}, key="hist_all")

# ─────────────────────────────────────────────
# フッター
# ─────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:1.5rem 0 0.5rem;font-size:0.65rem;color:#3a4a5a;">
  SLOTDASH &nbsp;|&nbsp; みんレポ差枚データ対応 &nbsp;|&nbsp; 個人利用専用<br>
  ※ このアプリはギャンブルを推奨するものではありません
</div>
""", unsafe_allow_html=True)
