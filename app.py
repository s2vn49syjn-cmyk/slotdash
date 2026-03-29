"""
スロダッシュ v3 - 島図機能追加版
Google Sheets連携 / スマホ最適化 / メモ・星印・島図機能付き
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
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# ★ 設定
# ─────────────────────────────────────────────
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"
SHEET_NAME = "スロデータ"

# ─────────────────────────────────────────────
# CSS
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
    max-width: 900px !important;
    margin: auto !important;
}
.neon-title { font-family: 'Orbitron', monospace; font-size: 1.5rem; font-weight: 900; color: #00ffcc; text-shadow: 0 0 10px #00ffcc88; letter-spacing: 2px; margin: 0; }
.neon-sub { font-size: 0.7rem; color: #7a8aaa; letter-spacing: 1px; }
.header-bar { background: linear-gradient(135deg, #0f1729 0%, #141c30 100%); border-bottom: 1px solid #00ffcc33; padding: 0.8rem 1rem; margin: -0.5rem -1rem 1rem -1rem; box-shadow: 0 4px 20px #00ffcc11; }
.card { background: linear-gradient(135deg, #111828 0%, #0d1520 100%); border: 1px solid #1e2d45; border-radius: 12px; padding: 1rem; margin-bottom: 0.8rem; position: relative; overflow: hidden; }
.card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, #00ffcc66, transparent); }
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
.section-title { font-family: 'Orbitron', monospace; font-size: 0.75rem; color: #00ffcc; letter-spacing: 2px; text-transform: uppercase; margin: 1.2rem 0 0.6rem; padding-bottom: 4px; border-bottom: 1px solid #00ffcc22; }
.memo-box { background: #0d1520; border: 1px solid #1e2d45; border-radius: 8px; padding: 8px 10px; font-size: 0.8rem; color: #a0b8d0; margin-top: 6px; }
.stButton > button { background: #111828 !important; border: 1px solid #1e2d45 !important; border-radius: 8px !important; color: #a0b0cc !important; font-size: 0.75rem !important; padding: 0.4rem 0.5rem !important; width: 100% !important; }
.stButton > button:hover { border-color: #00ffcc66 !important; color: #00ffcc !important; }
.stTabs [data-baseweb="tab-list"] { background: #0d1520 !important; border-radius: 10px !important; gap: 4px; padding: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px !important; color: #7a8aaa !important; font-size: 0.8rem !important; }
.stTabs [aria-selected="true"] { background: #1e2d45 !important; color: #00ffcc !important; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea { background-color: #111828 !important; border: 1px solid #1e2d45 !important; color: #e0e6f0 !important; border-radius: 8px !important; }
[data-testid="stMetric"] { background: #111828; border: 1px solid #1e2d45; border-radius: 10px; padding: 0.6rem 0.8rem; }
[data-testid="stMetricLabel"] { font-size: 0.7rem !important; color: #7a8aaa !important; }
[data-testid="stMetricValue"] { font-family: 'Orbitron', monospace !important; font-size: 1rem !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #1e2d45; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# コスモ堺 島定義（PDFを元に設定）
# 各島: {"name": 島名, "rows": [[台番, ...], [台番, ...]]}
# rowsの各リストが1列分の台番（上から下の順）
# ─────────────────────────────────────────────
DEFAULT_ISLANDS = [
    {"name": "島A (801-829)", "rows": [
        [801, 802, 803, 804, 805, 806, 807, 808, 809, 810],
        [811, 812, 813, 814, 815, 816, 817, 818, 819, 820],
    ]},
    {"name": "島B (821-851)", "rows": [
        [821, 822, 823, 824, 825, 826, 827, 828, 829, 830],
        [831, 832, 833, 834, 835, 836, 837, 838, 839, 840],
        [841, 842, 843, 844, 845, 846, 847, 848, 849, 850, 851],
    ]},
    {"name": "島C (852-899)", "rows": [
        [852, 853, 854, 855, 856, 857, 858, 859, 860, 861, 862, 863, 864, 865, 866, 867, 868, 869, 870],
        [871, 872, 873, 874, 875, 876, 877, 878, 879, 880, 881, 882, 883, 884, 885, 886, 887, 888, 889],
        [890, 891, 892, 893, 894, 895, 896, 897, 898, 899],
    ]},
    {"name": "島D (901-940)", "rows": [
        [901, 902, 903, 904, 905, 906, 907, 908, 909, 910],
        [911, 912, 913, 914, 915, 916, 917, 918, 919, 920],
        [921, 922, 923, 924, 925, 926, 927, 928, 929, 930],
        [931, 932, 933, 934, 935, 936, 937, 938, 939, 940],
    ]},
    {"name": "島E (941-999)", "rows": [
        [941, 942, 943, 944, 945, 946, 947, 948, 949, 950],
        [951, 952, 953, 954, 955, 956, 957, 958, 959, 960],
        [961, 962, 963, 964, 965, 966, 967, 968, 969, 970],
        [971, 972, 973, 974, 975, 976, 977, 978, 979, 980],
        [981, 982, 983, 984, 985, 986, 987, 988, 989, 990],
        [991, 992, 993, 994, 995, 996, 997, 998, 999],
    ]},
    {"name": "島F (1001-1060)", "rows": [
        [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010],
        [1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020],
        [1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030],
        [1031, 1032, 1033, 1034, 1035, 1036, 1037, 1038, 1039, 1040],
        [1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049, 1050],
        [1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1060],
    ]},
    {"name": "島G (1061-1120)", "rows": [
        [1061, 1062, 1063, 1064, 1065, 1066, 1067, 1068, 1069, 1070],
        [1071, 1072, 1073, 1074, 1075, 1076, 1077, 1078, 1079, 1080],
        [1081, 1082, 1083, 1084, 1085, 1086, 1087, 1088, 1089, 1090],
        [1091, 1092, 1093, 1094, 1095, 1096, 1097, 1098, 1099, 1100],
        [1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109, 1110],
        [1111, 1112, 1113, 1114, 1115, 1116, 1117, 1118, 1119, 1120],
    ]},
    {"name": "島H (1121-1220)", "rows": [
        [1121, 1122, 1123, 1124, 1125, 1126, 1127, 1128, 1129, 1130],
        [1131, 1132, 1133, 1134, 1135, 1136, 1137, 1138, 1139, 1140],
        [1141, 1142, 1143, 1144, 1145, 1146, 1147, 1148, 1149, 1150],
        [1151, 1152, 1153, 1154, 1155, 1156, 1157, 1158, 1159, 1160],
        [1161, 1162, 1163, 1164, 1165, 1166, 1167, 1168, 1169, 1170],
        [1171, 1172, 1173, 1174, 1175, 1176, 1177, 1178, 1179, 1180],
        [1181, 1182, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1190],
        [1191, 1192, 1193, 1194, 1195, 1196, 1197, 1198, 1199, 1200],
        [1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208, 1209, 1210],
        [1211, 1212, 1213, 1214, 1215, 1216, 1217, 1218, 1219, 1220],
    ]},
    {"name": "島I (1221-1304)", "rows": [
        [1221, 1222, 1223, 1224, 1225, 1226, 1227, 1228, 1229, 1230],
        [1231, 1232, 1233, 1234, 1235, 1236, 1237, 1238, 1239, 1240],
        [1241, 1242, 1243, 1244, 1245, 1246, 1247, 1248, 1249, 1250],
        [1251, 1252, 1253, 1254, 1255, 1256, 1257, 1258, 1259, 1260],
        [1261, 1262, 1263, 1264, 1265, 1266, 1267, 1268, 1269, 1270],
        [1271, 1272, 1273, 1274, 1275, 1276, 1277, 1278, 1279, 1280],
        [1281, 1282, 1283, 1284, 1285, 1286, 1287, 1288, 1289, 1290],
        [1291, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
        [1301, 1302, 1303, 1304],
    ]},
]

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

def diff_to_color(val):
    """差枚数をRGB色に変換"""
    if np.isnan(val):
        return "rgba(30,45,69,0.8)"  # グレー（データなし）
    if val >= 3000: return "rgba(0,200,100,0.95)"
    if val >= 1500: return "rgba(0,220,120,0.85)"
    if val >= 500:  return "rgba(100,220,150,0.75)"
    if val >= 0:    return "rgba(150,230,180,0.65)"
    if val >= -500: return "rgba(255,180,100,0.70)"
    if val >= -1500: return "rgba(255,120,80,0.80)"
    if val >= -3000: return "rgba(255,80,60,0.88)"
    return "rgba(220,40,40,0.95)"

def diff_to_text_color(val):
    if np.isnan(val): return "#7a8aaa"
    if val >= 500: return "#003820"
    if val >= 0: return "#004030"
    if val >= -500: return "#5a2000"
    return "#ffffff"

# ─────────────────────────────────────────────
# Google Sheets読み込み
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_from_sheets():
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
    df = pd.DataFrame()
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

    week_cols = []
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

    if not weekly_df.empty:
        df["週平均"] = weekly_df.mean(axis=1)
        trend_list = []
        for idx in weekly_df.index:
            vals = weekly_df.loc[idx].dropna().values
            trend_list.append(vals[-1] > vals[0] if len(vals) >= 3 else None)
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
# 島図生成
# ─────────────────────────────────────────────
def make_island_map(df, islands, selected_island_idx=None):
    """Plotlyで島図を生成"""
    diff_map = {}
    name_map = {}
    score_map = {}
    for _, row in df.iterrows():
        if not np.isnan(row["台番"]):
            num = int(row["台番"])
            diff_map[num] = row["前日差枚"]
            name_map[num] = row["機種名"]
            score_map[num] = row["スコア"]

    # 島ごとにPlotlyのshape+annotationで描画
    shapes = []
    annotations = []

    CELL_W = 52   # セル幅
    CELL_H = 38   # セル高さ
    GAP_X = 20    # 列間隔
    GAP_Y = 8     # 台間隔
    ISLAND_GAP_X = 60  # 島間隔（横）
    ISLAND_GAP_Y = 80  # 島間隔（縦）
    COLS_PER_ROW = 6   # 1行あたり最大島数

    island_positions = []
    cur_x, cur_y = 0, 0
    max_y_in_row = 0

    for i, island in enumerate(islands):
        if i % COLS_PER_ROW == 0 and i > 0:
            cur_x = 0
            cur_y -= max_y_in_row + ISLAND_GAP_Y
            max_y_in_row = 0

        island_positions.append((cur_x, cur_y))

        # この島の高さを計算
        max_rows = max(len(col) for col in island["rows"])
        island_h = max_rows * (CELL_H + GAP_Y)
        if island_h > max_y_in_row:
            max_y_in_row = island_h

        # この島の幅を計算
        island_w = len(island["rows"]) * (CELL_W + GAP_X)
        cur_x += island_w + ISLAND_GAP_X

    # 全体の範囲計算
    total_w = max(p[0] for p in island_positions) + 600
    total_h = abs(min(p[1] for p in island_positions)) + 300

    fig = go.Figure()
    fig.update_layout(
        width=max(800, total_w),
        height=max(600, total_h),
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0d1520",
        showlegend=False,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(visible=False, range=[-20, total_w]),
        yaxis=dict(visible=False, range=[-total_h + 50, 80]),
        hovermode="closest",
        font=dict(family="Noto Sans JP", color="#e0e6f0"),
    )

    # 各島を描画
    for i, (island, (ix, iy)) in enumerate(zip(islands, island_positions)):
        is_selected = (selected_island_idx == i)

        # 島ラベル
        annotations.append(dict(
            x=ix, y=iy + 20,
            text=f"<b>{island['name']}</b>",
            font=dict(size=10, color="#00ffcc" if is_selected else "#7a8aaa"),
            showarrow=False,
            xanchor="left",
        ))

        # 各列・各台を描画
        for col_idx, col_machines in enumerate(island["rows"]):
            cx = ix + col_idx * (CELL_W + GAP_X)
            for row_idx, machine_no in enumerate(col_machines):
                cy = iy - row_idx * (CELL_H + GAP_Y)

                diff = diff_map.get(machine_no, np.nan)
                machine_name = name_map.get(machine_no, "")
                score = score_map.get(machine_no, 50)
                bg_color = diff_to_color(diff)
                text_color = diff_to_text_color(diff)
                diff_text = diff_sign(diff) if not np.isnan(diff) else "?"

                # セルの背景
                shapes.append(dict(
                    type="rect",
                    x0=cx, y0=cy - CELL_H,
                    x1=cx + CELL_W, y1=cy,
                    fillcolor=bg_color,
                    line=dict(color="#ffffff22" if not is_selected else "#00ffcc44", width=0.5),
                    layer="below",
                ))

                # 台番
                annotations.append(dict(
                    x=cx + CELL_W / 2,
                    y=cy - 6,
                    text=f"<span style='font-size:7px;color:{text_color}88;'>{machine_no}</span>",
                    showarrow=False,
                    font=dict(size=7, color=text_color + "88" if len(text_color) == 7 else text_color),
                    xanchor="center",
                ))

                # 差枚数
                annotations.append(dict(
                    x=cx + CELL_W / 2,
                    y=cy - CELL_H / 2 - 4,
                    text=f"<b>{diff_text}</b>",
                    showarrow=False,
                    font=dict(size=9, color=text_color),
                    xanchor="center",
                ))

    fig.update_layout(shapes=shapes, annotations=annotations)
    return fig

# ─────────────────────────────────────────────
# セッションステート初期化
# ─────────────────────────────────────────────
if "stars" not in st.session_state:
    st.session_state.stars = {}
if "memos" not in st.session_state:
    st.session_state.memos = {}
if "active_filter" not in st.session_state:
    st.session_state.active_filter = "全台"
if "df_main" not in st.session_state:
    st.session_state.df_main = None
if "df_weekly" not in st.session_state:
    st.session_state.df_weekly = None
if "last_updated" not in st.session_state:
    st.session_state.last_updated = None
if "islands" not in st.session_state:
    st.session_state.islands = DEFAULT_ISLANDS

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
      <div class="neon-sub">{today_str} | コスモ堺 更新:{updated_str}</div>
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
tab_home, tab_island, tab_trend, tab_all, tab_memo, tab_island_edit = st.tabs([
    "🏠 ホーム", "🗺 島図", "📈 トレンド", "📋 全台", "⭐ メモ", "⚙ 島設定"
])

# ════════════════════════════════════════════
# 🏠 ホームタブ
# ════════════════════════════════════════════
with tab_home:
    df = st.session_state.df_main
    wdf = st.session_state.df_weekly

    if df is None:
        st.info("データを読み込み中です...")
    else:
        valid = df["前日差枚"].dropna()
        c1, c2, c3 = st.columns(3)
        c1.metric("総台数", f"{len(df)}台")
        c2.metric("プラス台", f"{(valid > 0).sum()}台")
        c3.metric("平均差枚", diff_sign(valid.mean()) if len(valid) > 0 else "-")

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
                        xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False,
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"spark_home_{idx}")

            btn_c1, btn_c2 = st.columns([1, 3])
            with btn_c1:
                if st.button(f"{star_icon} 星", key=f"star_home_{idx}"):
                    st.session_state.stars[台番_str] = not is_starred
                    st.rerun()
            with btn_c2:
                memo = st.session_state.memos.get(台番_str, "")
                if memo:
                    st.markdown(f'<div class="memo-box">📝 {memo}</div>', unsafe_allow_html=True)

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
# 🗺 島図タブ
# ════════════════════════════════════════════
with tab_island:
    df = st.session_state.df_main
    islands = st.session_state.islands

    if df is None:
        st.info("データを読み込み中です...")
    else:
        st.markdown('<div class="section-title">🗺 島図</div>', unsafe_allow_html=True)

        # カラーレジェンド
        st.markdown("""
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:0.8rem;font-size:0.7rem;">
          <span style="background:rgba(0,200,100,0.9);color:#003820;padding:2px 8px;border-radius:4px;font-weight:bold;">+3000以上</span>
          <span style="background:rgba(100,220,150,0.8);color:#003820;padding:2px 8px;border-radius:4px;">+500〜</span>
          <span style="background:rgba(150,230,180,0.65);color:#003820;padding:2px 8px;border-radius:4px;">0〜+500</span>
          <span style="background:rgba(255,180,100,0.7);color:#5a2000;padding:2px 8px;border-radius:4px;">0〜-500</span>
          <span style="background:rgba(255,80,60,0.88);color:#fff;padding:2px 8px;border-radius:4px;">-1500〜</span>
          <span style="background:rgba(220,40,40,0.95);color:#fff;padding:2px 8px;border-radius:4px;">-3000以下</span>
          <span style="background:rgba(30,45,69,0.8);color:#7a8aaa;padding:2px 8px;border-radius:4px;">データなし</span>
        </div>
        """, unsafe_allow_html=True)

        # 島フィルタ
        island_names = ["全島表示"] + [isl["name"] for isl in islands]
        sel_island = st.selectbox("島を選択", island_names, key="island_select")
        sel_island_idx = None
        if sel_island != "全島表示":
            sel_island_idx = island_names.index(sel_island) - 1
            display_islands = [islands[sel_island_idx]]
        else:
            display_islands = islands

        # 島図描画
        with st.spinner("島図を描画中..."):
            fig_map = make_island_map(df, display_islands, selected_island_idx=0 if sel_island_idx is not None else None)
            st.plotly_chart(fig_map, use_container_width=True, config={
                "displayModeBar": True,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                "displaylogo": False,
                "scrollZoom": True,
            })

        # 選択島の台一覧
        if sel_island != "全島表示" and sel_island_idx is not None:
            st.markdown(f'<div class="section-title">{sel_island} 台一覧</div>', unsafe_allow_html=True)
            island = islands[sel_island_idx]
            all_machines = [m for col in island["rows"] for m in col]
            island_df = df[df["台番"].apply(lambda x: int(x) if not np.isnan(x) else -1).isin(all_machines)].copy()
            if not island_df.empty:
                island_df = island_df.sort_values("前日差枚", ascending=False)
                disp = island_df[["台番", "機種名", "前日差枚", "スコア"]].copy()
                disp["台番"] = disp["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
                disp["前日差枚"] = disp["前日差枚"].apply(diff_sign)
                disp["スコア"] = disp["スコア"].apply(lambda x: f"{x:.0f}")
                st.dataframe(disp, hide_index=True, use_container_width=True, height=300)

# ════════════════════════════════════════════
# ⚙ 島設定タブ
# ════════════════════════════════════════════
with tab_island_edit:
    st.markdown('<div class="section-title">島の設定</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.75rem;color:#7a8aaa;margin-bottom:0.8rem;">島ごとに台番を設定できます。台番はカンマ区切りで入力してください。</div>', unsafe_allow_html=True)

    islands = st.session_state.islands

    # 島追加
    if st.button("➕ 島を追加", use_container_width=True):
        st.session_state.islands.append({
            "name": f"新しい島 {len(islands)+1}",
            "rows": [[]]
        })
        st.rerun()

    # 各島の編集
    for i, island in enumerate(islands):
        with st.expander(f"✏️ {island['name']}", expanded=False):
            new_name = st.text_input("島名", value=island["name"], key=f"island_name_{i}")
            st.session_state.islands[i]["name"] = new_name

            # 全台番をフラットに表示・編集
            all_machines = [str(m) for col in island["rows"] for m in col]
            machines_str = st.text_area(
                "台番（カンマ区切り）",
                value=", ".join(all_machines),
                height=80,
                key=f"island_machines_{i}",
                help="例: 901, 902, 903, 904, 905"
            )

            cols_count = st.number_input(
                "列数",
                min_value=1, max_value=20,
                value=len(island["rows"]),
                key=f"island_cols_{i}",
            )

            if st.button("💾 保存", key=f"save_island_{i}", use_container_width=True):
                try:
                    nums = [int(x.strip()) for x in machines_str.split(",") if x.strip().isdigit()]
                    # 台番を列数で均等分割
                    per_col = max(1, len(nums) // cols_count)
                    new_rows = []
                    for c in range(cols_count):
                        start = c * per_col
                        end = start + per_col if c < cols_count - 1 else len(nums)
                        if start < len(nums):
                            new_rows.append(nums[start:end])
                    st.session_state.islands[i]["rows"] = new_rows
                    st.success("✅ 保存しました")
                    st.rerun()
                except Exception as e:
                    st.error(f"エラー: {e}")

            if st.button("🗑 この島を削除", key=f"del_island_{i}", use_container_width=True):
                st.session_state.islands.pop(i)
                st.rerun()

    # デフォルトに戻す
    st.markdown("---")
    if st.button("🔄 デフォルト配置に戻す", use_container_width=True):
        st.session_state.islands = DEFAULT_ISLANDS
        st.success("デフォルト配置に戻しました")
        st.rerun()

# ════════════════════════════════════════════
# 📈 トレンドタブ
# ════════════════════════════════════════════
with tab_trend:
    df = st.session_state.df_main
    wdf = st.session_state.df_weekly

    if df is None:
        st.info("データを読み込み中です...")
    elif wdf is None or wdf.empty:
        st.warning("週次データがありません")
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

            fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.13)")
            fig.update_layout(
                height=320, paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1520",
                font=dict(family="Noto Sans JP", color="#a0b0cc", size=11),
                legend=dict(bgcolor="#111828", bordercolor="#1e2d45", borderwidth=1, font=dict(size=10), orientation="h", y=-0.25),
                xaxis=dict(showgrid=True, gridcolor="#1e2d45"),
                yaxis=dict(showgrid=True, gridcolor="#1e2d45", title="差枚数"),
                margin=dict(l=50, r=10, t=20, b=70),
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ════════════════════════════════════════════
# 📋 全台一覧タブ
# ════════════════════════════════════════════
with tab_all:
    df = st.session_state.df_main
    if df is None:
        st.info("データを読み込み中です...")
    else:
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
        df_v = df_v.sort_values(sort_by, ascending=asc, na_position="last")

        st.markdown(f'<div style="font-size:0.75rem;color:#7a8aaa;margin:0.3rem 0;">{len(df_v)} 台表示中</div>', unsafe_allow_html=True)
        disp = df_v[["台番", "機種名", "前日差枚", "週平均", "スコア", "回転数"]].copy()
        disp["台番"] = disp["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
        disp["前日差枚"] = disp["前日差枚"].apply(diff_sign)
        disp["週平均"] = disp["週平均"].apply(diff_sign)
        disp["スコア"] = disp["スコア"].apply(lambda x: f"{x:.0f}")
        disp["回転数"] = disp["回転数"].apply(lambda x: f"{int(x):,}" if not np.isnan(x) else "-")
        st.dataframe(disp, hide_index=True, use_container_width=True, height=400)

        st.markdown('<div class="section-title">差枚分布</div>', unsafe_allow_html=True)
        vals = df_v["前日差枚"].dropna()
        if len(vals) > 0:
            fig_h = go.Figure(go.Histogram(
                x=vals, nbinsx=20,
                marker_color=["#00ff88" if v >= 0 else "#ff4444" for v in vals],
                opacity=0.8,
            ))
            fig_h.add_vline(x=0, line_dash="dash", line_color="rgba(255,255,255,0.25)")
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

        machine_options = df.apply(
            lambda r: f"#{int(r['台番']) if not np.isnan(r['台番']) else '?'} {r['機種名']}", axis=1
        ).tolist()
        sel_machine = st.selectbox("台を選択", machine_options)
        sel_idx = machine_options.index(sel_machine)
        row = df.iloc[sel_idx]
        台番_str = str(int(row["台番"])) if not np.isnan(row["台番"]) else "?"

        is_starred = st.session_state.stars.get(台番_str, False)
        star_label = "⭐ 星印ON（タップでOFF）" if is_starred else "☆ 星印OFF（タップでON）"
        if st.button(star_label, use_container_width=True):
            st.session_state.stars[台番_str] = not is_starred
            st.rerun()

        current_memo = st.session_state.memos.get(台番_str, "")
        new_memo = st.text_area("メモ", value=current_memo, height=100, key=f"memo_input_{台番_str}")
        if st.button("💾 メモを保存", use_container_width=True):
            st.session_state.memos[台番_str] = new_memo
            st.success("保存しました")

        st.markdown('<div class="section-title">星印一覧</div>', unsafe_allow_html=True)
        starred_list = [(k, v) for k, v in st.session_state.stars.items() if v]
        if starred_list:
            for 台番_s, _ in starred_list:
                memo = st.session_state.memos.get(台番_s, "")
                matched = df[df["台番"].apply(lambda x: str(int(x)) if not np.isnan(x) else "") == 台番_s]
                機種 = matched.iloc[0]["機種名"] if len(matched) > 0 else "?"
                diff = matched.iloc[0]["前日差枚"] if len(matched) > 0 else np.nan
                dc = diff_class(diff)
                st.markdown(f"""
                <div class="card">
                  <div style="display:flex;justify-content:space-between;">
                    <div><div class="machine-num">⭐ 台番 {台番_s}</div><div class="machine-name">{機種}</div></div>
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
  SLOTDASH v3 | スーパーコスモ堺専用 | 個人利用専用<br>
  ※ このアプリはギャンブルを推奨するものではありません
</div>
""", unsafe_allow_html=True)
