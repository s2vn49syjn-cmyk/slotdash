"""
スロダッシュ v4 - アラート・据え置き判別・日付別蓄積対応版
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="スロダッシュ | コスモ堺", page_icon="🎰", layout="wide", initial_sidebar_state="collapsed")

SPREADSHEET_ID = "1Hak9Q7Q_kjbp22A59pAUJ2twrEy4mdXk1sBfLYlynR8"
JUGGLER_KEYWORDS = ["ジャグラー", "juggler", "JUGGLER"]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+JP:wght@300;400;700&display=swap');
html, body, [class*="css"] { background-color: #0a0e1a !important; color: #e0e6f0 !important; font-family: 'Noto Sans JP', sans-serif !important; }
.main .block-container { padding: 0.5rem 1rem 2rem 1rem !important; max-width: 900px !important; margin: auto !important; }
.neon-title { font-family: 'Orbitron', monospace; font-size: 1.5rem; font-weight: 900; color: #00ffcc; text-shadow: 0 0 10px #00ffcc88; letter-spacing: 2px; margin: 0; }
.neon-sub { font-size: 0.7rem; color: #7a8aaa; }
.header-bar { background: linear-gradient(135deg, #0f1729 0%, #141c30 100%); border-bottom: 1px solid #00ffcc33; padding: 0.8rem 1rem; margin: -0.5rem -1rem 1rem -1rem; box-shadow: 0 4px 20px #00ffcc11; }
.card { background: linear-gradient(135deg, #111828 0%, #0d1520 100%); border: 1px solid #1e2d45; border-radius: 12px; padding: 1rem; margin-bottom: 0.8rem; position: relative; overflow: hidden; }
.card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, #00ffcc66, transparent); }
.card-hot::before { background: linear-gradient(90deg, transparent, #00ff8866, transparent); }
.card-cold::before { background: linear-gradient(90deg, transparent, #ff444466, transparent); }
.alert-card { background: linear-gradient(135deg, #1a1020 0%, #140d1a 100%); border: 1px solid #ff444433; border-radius: 10px; padding: 0.7rem 1rem; margin-bottom: 0.5rem; }
.alert-card-green { background: linear-gradient(135deg, #0a1a10 0%, #0d1a10 100%); border: 1px solid #00ff8833; border-radius: 10px; padding: 0.7rem 1rem; margin-bottom: 0.5rem; }
.alert-card-blue { background: linear-gradient(135deg, #0a1020 0%, #0d1525 100%); border: 1px solid #00ccff33; border-radius: 10px; padding: 0.7rem 1rem; margin-bottom: 0.5rem; }
.alert-card-star { background: linear-gradient(135deg, #1a1a0a 0%, #1a1505 100%); border: 1px solid #ffcc0033; border-radius: 10px; padding: 0.7rem 1rem; margin-bottom: 0.5rem; }
.machine-num { font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #7a8aaa; }
.machine-name { font-size: 1rem; font-weight: 700; color: #c8d8f0; margin: 2px 0 4px; }
.diff-plus { font-family: 'Orbitron', monospace; font-size: 1.4rem; font-weight: 900; color: #00ff88; }
.diff-minus { font-family: 'Orbitron', monospace; font-size: 1.4rem; font-weight: 900; color: #ff4444; }
.diff-neutral { font-family: 'Orbitron', monospace; font-size: 1.4rem; font-weight: 900; color: #ffcc00; }
.score-bar-wrap { background: #0a0e1a; border-radius: 6px; height: 6px; margin-top: 6px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 6px; }
.badge { display: inline-block; font-size: 0.65rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; margin-right: 4px; margin-bottom: 2px; }
.badge-hot { background: #00ff8822; color: #00ff88; border: 1px solid #00ff8844; }
.badge-cold { background: #ff444422; color: #ff6666; border: 1px solid #ff444444; }
.badge-star { background: #ffcc0022; color: #ffcc00; border: 1px solid #ffcc0044; }
.badge-juggler { background: #8844ff22; color: #aa88ff; border: 1px solid #8844ff44; }
.badge-hold { background: #00ccff22; color: #00ccff; border: 1px solid #00ccff44; }
.badge-danger { background: #ff000022; color: #ff4444; border: 1px solid #ff000044; }
.section-title { font-family: 'Orbitron', monospace; font-size: 0.75rem; color: #00ffcc; letter-spacing: 2px; text-transform: uppercase; margin: 1.2rem 0 0.6rem; padding-bottom: 4px; border-bottom: 1px solid #00ffcc22; }
.memo-box { background: #0d1520; border: 1px solid #1e2d45; border-radius: 8px; padding: 8px 10px; font-size: 0.8rem; color: #a0b8d0; margin-top: 6px; }
.hold-score { font-family: 'Orbitron', monospace; font-size: 1.1rem; font-weight: 900; color: #00ccff; }
.stButton > button { background: #111828 !important; border: 1px solid #1e2d45 !important; border-radius: 8px !important; color: #a0b0cc !important; font-size: 0.75rem !important; padding: 0.4rem 0.5rem !important; width: 100% !important; }
.stButton > button:hover { border-color: #00ffcc66 !important; color: #00ffcc !important; }
.stTabs [data-baseweb="tab-list"] { background: #0d1520 !important; border-radius: 10px !important; gap: 4px; padding: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px !important; color: #7a8aaa !important; font-size: 0.75rem !important; }
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
# ユーティリティ
# ─────────────────────────────────────────────
def parse_num(val):
    if val is None: return np.nan
    if isinstance(val, (int, float)):
        try:
            f = float(val)
            return f if not (f != f) else np.nan  # NaN check
        except: return np.nan
    s = str(val).strip()
    if s in ["-", "", "None", "ー", "−", "nan", "NaN"]: return np.nan
    s = s.replace("，", ",").replace("＋", "+").replace("－", "-").replace("ー", "-").replace("−", "-").replace(",", "")
    m = re.search(r"[+-]?\d+\.?\d*", s)
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
    """PDFの凡例に合わせた色設定"""
    if np.isnan(val): return "#f0f0f0"        # 白（未表示）
    if val >= 10000: return "#111111"          # 黒背景（+10000以上）
    if val >= 5000: return "#8B0000"           # 濃い赤（+5000〜+9999）
    if val >= 4000: return "#CC0000"           # 赤（+4000〜+4999）
    if val >= 3000: return "#CC44CC"           # 紫（+3000〜+3999）
    if val >= 2000: return "#66BB44"           # 黄緑（+2000〜+2999）
    if val >= 1000: return "#DDDD00"           # 黄色（+1000〜+1999）
    if val >= 1: return "#88CCEE"              # 水色（+1〜+999）
    if val == 0: return "#f0f0f0"              # 白（0・未表示）
    if val >= -499: return "#ffffff"           # 白（-1〜-499）
    return "#ffffff"                           # 白枠（-500以下）

def diff_to_text_color(val):
    """PDFの凡例に合わせたテキスト色"""
    if np.isnan(val): return "#999999"
    if val >= 10000: return "#FF4444"          # 黒背景→赤文字
    if val >= 5000: return "#ffffff"           # 白文字
    if val >= 4000: return "#ffffff"           # 白文字
    if val >= 3000: return "#ffffff"           # 白文字
    if val >= 2000: return "#ffffff"           # 白文字
    if val >= 1000: return "#333333"           # 黒文字
    if val >= 1: return "#333333"              # 黒文字
    if val == 0: return "#999999"              # グレー文字
    if val >= -499: return "#333333"           # 黒文字（小マイナス）
    return "#CC0000"                           # 赤文字（大マイナス）

# ─────────────────────────────────────────────
# Google Sheets: 最新シート読み込み
# ─────────────────────────────────────────────
def get_gspread_client():
    creds_dict = st.secrets["gcp_service_account"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_latest_sheet():
    """最新の日付シートを読み込む"""
    try:
        client = get_gspread_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        all_ws = spreadsheet.worksheets()
        # 日付シート優先、なければスロデータ
        date_sheets = sorted([ws for ws in all_ws if re.match(r"\d{4}-\d{2}-\d{2}", ws.title)], key=lambda w: w.title)
        if date_sheets:
            sheet = date_sheets[-1]
        else:
            sheet = spreadsheet.worksheet("スロデータ")
        data = sheet.get_all_records()
        if not data:
            return None, f"シート「{sheet.title}」にデータがありません"
        return pd.DataFrame(data), None
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=300)
def load_history(max_days=7):
    """直近7日分の履歴を読み込み（3日/7日集計に最適化）"""
    try:
        client = get_gspread_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        all_ws = spreadsheet.worksheets()
        
        # 日付シートを新しい順に取得
        date_sheets = sorted(
            [ws for ws in all_ws if re.match(r"\d{4}-\d{2}-\d{2}", ws.title)],
            key=lambda w: w.title, reverse=True
        )[:max_days]
        
        history = {}
        date_labels = [ws.title for ws in date_sheets]
        
        for ws in date_sheets:
            try:
                data = ws.get_all_records()
                if not data:
                    continue
                df = pd.DataFrame(data)
                cols = {c.strip(): c for c in df.columns}
                
                def fc(*keys):
                    for k in keys:
                        for c in cols:
                            if k in c: return cols[c]
                    return None
                
                台番col = fc("台番", "台no")
                差枚col = fc("差枚", "前日差枚")
                回転col = fc("回転数", "回転", "G数")
                
                if not 台番col or not 差枚col:
                    continue
                
                for _, row in df.iterrows():
                    try:
                        num = int(parse_num(row[台番col]))
                        diff = parse_num(row[差枚col])
                        rot = parse_num(row[回転col]) if 回転col else np.nan
                        
                        if num not in history:
                            history[num] = {}
                        history[num][ws.title] = {"diff": diff, "rot": rot}
                    except:
                        continue
            except:
                continue
        return history, date_labels
    except Exception as e:
        st.warning(f"履歴読み込みエラー: {e}")
        return {}, []

def process_df(df_raw):
    df = pd.DataFrame()
    cols = {c.strip(): c for c in df_raw.columns}
    def fc(*keys):
        for k in keys:
            for c in cols:
                if k in c: return cols[c]
        return None
    台番col = fc("台番", "台no", "No")
    機種col = fc("機種名", "機種", "name")
    差枚col = fc("差枚", "前日差枚")
    回転col = fc("回転数", "回転", "G数")
    ボーナスcol = fc("ボーナス", "bonus")
    if not 台番col or not 機種col:
        return None, None
    df["台番"] = df_raw[台番col].apply(parse_num)
    df["機種名"] = df_raw[機種col].astype(str).str.strip()
    df["前日差枚"] = df_raw[差枚col].apply(parse_num) if 差枚col else np.nan
    df["回転数"] = df_raw[回転col].apply(parse_num) if 回転col else np.nan
    df["ボーナス"] = df_raw[ボーナスcol].apply(parse_num) if ボーナスcol else np.nan
    df["週平均"] = df["前日差枚"]
    df["スコア"] = [calc_score(df.loc[i, "前日差枚"], np.nan, None) for i in df.index]
    df["is_juggler"] = df["機種名"].apply(is_juggler)
    df.index = range(len(df))
    return df, pd.DataFrame()

# ─────────────────────────────────────────────
# アラート計算
# ─────────────────────────────────────────────
def calc_alerts(df_today, history, stars):
    alerts = []
    hold_candidates = []

    for _, row in df_today.iterrows():
        if np.isnan(row["台番"]): continue
        num = int(row["台番"])
        台番_str = str(num)
        機種 = row["機種名"]
        today_diff = row["前日差枚"]

        machine_hist = history.get(num, {})
        sorted_dates = sorted(machine_hist.keys())
        diffs = [machine_hist[d]["diff"] for d in sorted_dates if not np.isnan(machine_hist[d]["diff"])]
        rots = [machine_hist[d]["rot"] for d in sorted_dates if not np.isnan(machine_hist[d].get("rot", np.nan))]

        # アラート1: 連続凹み3日以上
        if len(diffs) >= 3 and all(d < 0 for d in diffs[-3:]):
            alerts.append({"type": "cold", "icon": "❄️", "label": f"連続凹み{sum(1 for d in diffs if d<0)}日",
                "台番": num, "機種名": 機種, "diff": today_diff,
                "detail": " / ".join([diff_sign(d) for d in diffs[-3:]])})

        # アラート2: 連続プラス3日以上
        elif len(diffs) >= 3 and all(d > 0 for d in diffs[-3:]):
            alerts.append({"type": "hot", "icon": "🔥", "label": f"連続好調{sum(1 for d in diffs if d>0)}日",
                "台番": num, "機種名": 機種, "diff": today_diff,
                "detail": " / ".join([diff_sign(d) for d in diffs[-3:]])})

        # アラート3: 大幅凹み
        if not np.isnan(today_diff) and today_diff <= -3000:
            alerts.append({"type": "danger", "icon": "⚠️", "label": "大幅凹み",
                "台番": num, "機種名": 機種, "diff": today_diff,
                "detail": f"前日差枚 {diff_sign(today_diff)}"})

        # アラート4: 星印台の急変動
        if stars.get(台番_str) and len(diffs) >= 2:
            change = diffs[-1] - diffs[-2]
            if abs(change) >= 2000:
                direction = "急上昇" if change > 0 else "急落下"
                alerts.append({"type": "star", "icon": "⭐", "label": f"注目台が{direction}",
                    "台番": num, "機種名": 機種, "diff": today_diff,
                    "detail": f"前日比 {diff_sign(change)}"})

        # 据え置きスコア計算
        plus_days = sum(1 for d in diffs if d > 0)
        hold_score = min(100, plus_days * 15
            + (20 if rots and np.mean(rots) >= 600 else 0)
            + (15 if diffs and np.mean(diffs) > 500 else 0)
            + (20 if not np.isnan(today_diff) and today_diff >= 2000 else 0))

        if hold_score >= 50:
            hold_candidates.append({
                "台番": num, "機種名": 機種,
                "据え置きスコア": hold_score,
                "diff": today_diff,
                "連続プラス日": plus_days,
                "週平均": np.mean(diffs) if diffs else np.nan,
            })

    hold_candidates.sort(key=lambda x: x["据え置きスコア"], reverse=True)
    return alerts, hold_candidates[:10]

# ─────────────────────────────────────────────
# 島定義
# ─────────────────────────────────────────────
DEFAULT_ISLANDS = [
    # 島1: 875〜955（左端・縦2列）
    {
        "name": "875〜955",
        "pos": (0, 0),
        "rows": [
            [911,912,913,914,915,916,917,918,919,920,921,922,923,924,925,926,927,928,929,930,931,932,933,934,935,936,937,938,939,940,941,942,943,944],
            [875,876,877,878,879,880,881,882,883,884,885,886,887,888,889,890,891,892,893,894,895,896,897,898,899,900,901,902,903,904,905,906,907,908,909,910],
            [945,946,947,948,949,950,951,952,953,954,955],
        ]
    },
    # 島2: 839〜874（縦3列）
    {
        "name": "839〜874",
        "pos": (1, 0),
        "rows": [
            [841,842,843,844,845,846,847,848,849,850,851,852,853,854,855,856,857,858,859,860,861,862,863,864,865,866,867,868,869,870,871,872],
            [839,840],
            [873,874],
        ]
    },
    # 島3: 801〜838（縦1列）
    {
        "name": "801〜838",
        "pos": (2, 0),
        "rows": [
            [801,802,803,804,805,806,807,808,809,810,811,812,813,814,815,816,817,818,819,820,821,822,823,824,825,826,827,828,829,830,831,832,833,834,835,836,837,838],
        ]
    },
    # 島4: 982〜1020（縦列・右向き2台ずつ）
    {
        "name": "982〜1020",
        "pos": (3, 0),
        "rows": [
            [982,983,984,985,986,987,988,989],
            [1010,1011,1012,1013,1014,1015,1016,1017,1018,1019,1020],
        ]
    },
    # 島5: 990〜1009（対面2列）
    {
        "name": "990〜1009",
        "pos": (0, -1),
        "rows": [
            [990,991,992,993,994,995,996,997,998,999],
            [1000,1001,1002,1003,1004,1005,1006,1007,1008,1009],
        ]
    },
    # 島6: 1065〜1109（縦列）
    {
        "name": "1065〜1109",
        "pos": (1, -1),
        "rows": [
            [1065,1066,1067,1068,1069,1070,1071,1072,1073,1074,1075,1076],
            [1077,1078,1079,1080,1081,1082,1083,1084,1085,1086,1087,1088,1089],
            [1090,1091,1092,1093,1094,1095,1096,1097,1098,1099,1100],
            [1101,1102,1103,1104,1105,1106,1107,1108,1109],
        ]
    },
    # 島7: 1116〜1131（対面2列）
    {
        "name": "1116〜1131",
        "pos": (0, -2),
        "rows": [
            [1116,1117,1118,1119,1120,1121,1122,1123,1124],
            [1125,1126,1127,1128,1129,1130,1131],
        ]
    },
    # 島8: 1110〜1149（縦多列）
    {
        "name": "1110〜1149",
        "pos": (1, -2),
        "rows": [
            [1110,1111,1112,1113,1114,1115],
            [1132,1133,1134,1135,1136,1137,1138,1139,1140],
            [1141,1142,1143,1144,1145,1146,1147,1148,1149],
        ]
    },
    # 島9: 1200〜1212（対面2列）
    {
        "name": "1200〜1212",
        "pos": (2, -2),
        "rows": [
            [1200,1201,1202,1203,1204,1205,1206],
            [1207,1208,1209,1210,1211,1212],
        ]
    },
    # 島10: 1150〜1199（縦多列）
    {
        "name": "1150〜1199",
        "pos": (3, -1),
        "rows": [
            [1150,1151,1152,1153,1154,1155,1156,1157,1158,1159,1160],
            [1161,1162,1163,1164,1165,1166,1167,1168,1169,1170],
            [1171,1172,1173,1174,1175,1176,1177,1178,1179,1180],
            [1181,1182,1183,1184,1185,1186,1187,1188,1189,1190,1191],
            [1192,1193,1194,1195,1196,1197,1198,1199],
        ]
    },
    # 島11: 1213〜1232（縦列）
    {
        "name": "1213〜1232",
        "pos": (3, -2),
        "rows": [
            [1213,1214,1215,1216,1217,1218,1219,1220],
            [1221,1222,1223,1224,1225,1226,1227,1228,1229,1230,1231,1232],
        ]
    },
    # 島12: 1233〜1260（縦列）
    {
        "name": "1233〜1260",
        "pos": (2, -3),
        "rows": [
            [1233,1234,1235,1236,1237,1238,1239,1240],
            [1241,1242,1243,1244,1245,1246,1247,1248,1249,1250],
            [1251,1252,1253,1254,1255,1256,1257,1258,1259,1260],
        ]
    },
    # 島13: 1261〜1304（縦列）
    {
        "name": "1261〜1304",
        "pos": (0, -3),
        "rows": [
            [1261,1262,1263,1264,1265,1266,1267,1268,1269,1270],
            [1271,1272,1273,1274,1275,1276,1277,1278,1279,1280],
            [1281,1282,1283,1284,1285,1286,1287,1288,1289,1290],
            [1291,1292,1293,1294,1295,1296,1297,1298,1299,1300],
            [1301,1302,1303,1304],
        ]
    },
]

def make_island_map(df, islands, target_machines=None, diff_override=None):
    """
    島図をPlotlyで描画
    target_machines: 狙い台リスト（台番のset）- 枠線で強調表示
    diff_override: {台番: 差枚} の辞書。指定時はこちらの値を使って色分け
    """
    diff_map = {}
    name_map = {}
    for _, row in df.iterrows():
        if not np.isnan(row["台番"]):
            n = int(row["台番"])
            diff_map[n] = row["前日差枚"]
            name_map[n] = row["機種名"]

    # 集計値が指定されていればdiff_mapを上書き
    if diff_override:
        for n, v in diff_override.items():
            diff_map[n] = v

    if target_machines is None:
        target_machines = set()

    shapes, annotations = [], []
    CELL_W, CELL_H = 62, 46
    GAP_X, GAP_Y = 3, 3
    # pos座標を実際のピクセル座標に変換するスケール
    SCALE_X = 220  # 島間の横間隔
    SCALE_Y = 550  # 島間の縦間隔

    # 各島の絶対座標を計算（pos指定ベース）
    island_coords = []
    for isl in islands:
        pos = isl.get("pos", (0, 0))
        ix = pos[0] * SCALE_X
        iy = pos[1] * SCALE_Y
        island_coords.append((ix, iy))

    # 全体の範囲
    all_x = [c[0] for c in island_coords]
    all_y = [c[1] for c in island_coords]
    total_w = max(all_x) + SCALE_X + 50
    total_h = abs(min(all_y)) + SCALE_Y + 50

    fig = go.Figure()
    fig.update_layout(
        width=max(700, total_w),
        height=max(600, total_h),
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0d1520",
        showlegend=False,
        margin=dict(l=5, r=5, t=10, b=5),
        xaxis=dict(visible=False, range=[-10, total_w]),
        yaxis=dict(visible=False, range=[-total_h+30, 80]),
        hovermode="closest",
    )

    for isl, (ix, iy) in zip(islands, island_coords):
        # 島ラベル
        annotations.append(dict(
            x=ix, y=iy + 22,
            text=f"<b>{isl['name']}</b>",
            font=dict(size=10, color="#00ffcc"),
            showarrow=False, xanchor="left"
        ))

        for ci, col_machines in enumerate(isl["rows"]):
            cx = ix + ci * (CELL_W + GAP_X)
            for ri, mno in enumerate(col_machines):
                cy = iy - ri * (CELL_H + GAP_Y)
                diff = diff_map.get(mno, np.nan)
                bg = diff_to_color(diff)
                text_c = diff_to_text_color(diff)
                is_target = mno in target_machines

                # 差枚テキスト
                if np.isnan(diff):
                    diff_text = "?"
                elif diff >= 0:
                    diff_text = f"+{int(diff):,}"
                else:
                    diff_text = f"{int(diff):,}"

                # 枠線
                if not np.isnan(diff) and diff <= -500:
                    border_color = "rgba(200,0,0,0.7)"
                    border_w = 1.5
                else:
                    border_color = "rgba(0,0,0,0.2)"
                    border_w = 0.8

                shapes.append(dict(
                    type="rect",
                    x0=cx, y0=cy - CELL_H,
                    x1=cx + CELL_W, y1=cy,
                    fillcolor=bg,
                    line=dict(color=border_color, width=border_w),
                    layer="below"
                ))

                # 狙い台：白い外枠＋金色内枠で二重枠にして目立たせる
                if is_target:
                    # 外側の白枠
                    shapes.append(dict(
                        type="rect",
                        x0=cx - 3, y0=cy - CELL_H - 3,
                        x1=cx + CELL_W + 3, y1=cy + 3,
                        fillcolor="rgba(0,0,0,0)",
                        line=dict(color="#ffffff", width=3),
                        layer="above"
                    ))
                    # 内側の金枠
                    shapes.append(dict(
                        type="rect",
                        x0=cx - 1, y0=cy - CELL_H - 1,
                        x1=cx + CELL_W + 1, y1=cy + 1,
                        fillcolor="rgba(0,0,0,0)",
                        line=dict(color="#FFD700", width=2),
                        layer="above"
                    ))
                    # 🎯マーク
                    annotations.append(dict(
                        x=cx + CELL_W/2, y=cy + 10,
                        text="🎯",
                        showarrow=False,
                        font=dict(size=11),
                        xanchor="center"
                    ))

                # 台番（上部）
                num_color = "#ffffff" if not np.isnan(diff) and diff >= 10000 else "rgba(0,0,0,0.55)"
                annotations.append(dict(
                    x=cx + CELL_W/2, y=cy - 9,
                    text=str(mno),
                    showarrow=False,
                    font=dict(size=9, color=num_color),
                    xanchor="center"
                ))

                # 差枚（中央）
                annotations.append(dict(
                    x=cx + CELL_W/2, y=cy - CELL_H/2 - 3,
                    text=f"<b>{diff_text}</b>",
                    showarrow=False,
                    font=dict(size=10, color=text_c),
                    xanchor="center"
                ))

    fig.update_layout(shapes=shapes, annotations=annotations)
    return fig


# ─────────────────────────────────────────────
# セッションステート
# ─────────────────────────────────────────────
for key, val in [("stars",{}),("memos",{}),("active_filter","全台"),
                  ("df_main",None),("df_weekly",None),("last_updated",None),
                  ("islands",DEFAULT_ISLANDS)]:
    if key not in st.session_state:
        st.session_state[key] = val

def load_data():
    with st.spinner("データ取得中..."):
        df_raw, err = load_latest_sheet()
        if err:
            st.error(f"❌ {err}"); return
        df, wdf = process_df(df_raw)
        if df is None:
            st.error("❌ データの列が認識できませんでした"); return
        st.session_state.df_main = df
        st.session_state.df_weekly = wdf if wdf is not None else pd.DataFrame()
        st.session_state.last_updated = datetime.now().strftime("%H:%M")

if st.session_state.df_main is None:
    load_data()

# ─────────────────────────────────────────────
# ヘッダー
# ─────────────────────────────────────────────
today_str = datetime.now().strftime("%Y年%-m月%-d日")
col_h1, col_h2 = st.columns([3,1])
with col_h1:
    st.markdown(f"""<div class="header-bar">
      <div class="neon-title">🎰 SLOTDASH</div>
      <div class="neon-sub">{today_str} | コスモ堺 更新:{st.session_state.last_updated or "-"}</div>
    </div>""", unsafe_allow_html=True)
with col_h2:
    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
    if st.button("🔄 更新", use_container_width=True):
        st.cache_data.clear(); load_data(); st.rerun()

# ─────────────────────────────────────────────
# タブ
# ─────────────────────────────────────────────
tab_home, tab_alert, tab_hold, tab_island, tab_trend, tab_all, tab_memo, tab_island_edit = st.tabs([
    "🏠 ホーム", "🔔 アラート", "🎯 据え置き", "🗺 島図", "📈 トレンド", "📋 全台", "⭐ メモ", "⚙ 島設定"
])

# ════════════════════════════════════════════
# 🏠 ホームタブ
# ════════════════════════════════════════════
with tab_home:
    df = st.session_state.df_main
    if df is None:
        st.info("データを読み込み中です...")
    else:
        valid = df["前日差枚"].dropna()
        minus_count = (valid < 0).sum()
        plus_count = (valid > 0).sum()
       
        c1, c2, c3 = st.columns(3)
        c1.metric("総台数", f"{len(df)}台")
        c2.metric("プラス/マイナス", f"{plus_count}/{minus_count}")
        c3.metric("平均差枚", diff_sign(valid.mean()) if len(valid) > 0 else "-")

        # ── 直近傾向まとめ（朝イチ参考） ──
        st.markdown('<div class="section-title">📅 直近傾向まとめ（朝イチ参考）</div>', unsafe_allow_html=True)
        
        history, date_labels = load_history()
        
        if history and len(date_labels) >= 3:
            summary_data = []
            for _, row in df.iterrows():
                if np.isnan(row["台番"]):
                    continue
                num = int(row["台番"])
                machine_hist = history.get(num, {})
               
                sorted_dates = sorted(machine_hist.keys(), reverse=True)
               
                recent3 = sorted_dates[:3]
                sum3 = sum(machine_hist[d]["diff"] for d in recent3 if not np.isnan(machine_hist[d]["diff"]))
               
                recent7 = sorted_dates[:7]
                sum7 = sum(machine_hist[d]["diff"] for d in recent7 if not np.isnan(machine_hist[d]["diff"]))
               
                rots_recent = [machine_hist[d].get("rot", np.nan) for d in recent3]
                valid_rots = [r for r in rots_recent if not np.isnan(r)]
                high_rot_days = len([r for r in valid_rots if r >= 600])
                avg_rot = round(np.mean(valid_rots)) if valid_rots else np.nan
               
                summary_data.append({
                    "台番": num,
                    "機種名": row["機種名"],
                    "直近3日合計": sum3,
                    "直近7日合計": sum7,
                    "高回転日数(3日)": high_rot_days,
                    "平均回転(3日)": avg_rot if not np.isnan(avg_rot) else "-",
                    "前日差枚": row["前日差枚"]
                })
           
            summary_df = pd.DataFrame(summary_data)
           
            col3, col7 = st.columns(2)
            with col3:
                st.markdown('<div style="font-size:0.82rem;color:#00ffcc;margin-bottom:4px;">📈 直近3日間 好調台 TOP5</div>', unsafe_allow_html=True)
                top3 = summary_df.nlargest(5, "直近3日合計")[["台番", "機種名", "直近3日合計", "前日差枚"]].copy()
                top3["台番"] = top3["台番"].astype(int)
                top3["直近3日合計"] = top3["直近3日合計"].apply(diff_sign)
                top3["前日差枚"] = top3["前日差枚"].apply(diff_sign)
                st.dataframe(top3, hide_index=True, use_container_width=True, height=220)
            
            with col7:
                st.markdown('<div style="font-size:0.82rem;color:#00ffcc;margin-bottom:4px;">📈 直近7日間 好調台 TOP5</div>', unsafe_allow_html=True)
                top7 = summary_df.nlargest(5, "直近7日合計")[["台番", "機種名", "直近7日合計", "前日差枚"]].copy()
                top7["台番"] = top7["台番"].astype(int)
                top7["直近7日合計"] = top7["直近7日合計"].apply(diff_sign)
                top7["前日差枚"] = top7["前日差枚"].apply(diff_sign)
                st.dataframe(top7, hide_index=True, use_container_width=True, height=220)
           
            st.markdown('<div class="section-title">🔄 連日高回転台（朝イチ据え置き期待）</div>', unsafe_allow_html=True)
            high_rot_df = summary_df[summary_df["高回転日数(3日)"] >= 2].sort_values("高回転日数(3日)", ascending=False)
           
            if not high_rot_df.empty:
                high_disp = high_rot_df[["台番", "機種名", "高回転日数(3日)", "平均回転(3日)", "直近3日合計"]].head(12).copy()
                high_disp["台番"] = high_disp["台番"].astype(int)
                high_disp["直近3日合計"] = high_disp["直近3日合計"].apply(diff_sign)
                st.dataframe(high_disp, hide_index=True, use_container_width=True, height=320)
            else:
                st.info("直近3日間で高回転（600G以上）が続いている台はまだありません。")
           
            if st.button("🌟 上位好調台をすべて星印に登録（3日+7日トップ各5台）", use_container_width=True):
                top_nums = set(summary_df.nlargest(5, "直近3日合計")["台番"]) | \
                           set(summary_df.nlargest(5, "直近7日合計")["台番"])
                for n in top_nums:
                    st.session_state.stars[str(int(n))] = True
                st.success(f"{len(top_nums)}台を星印に登録しました！")
                st.rerun()
       
        else:
            st.info("📅 直近傾向まとめは、3日以上の履歴データが蓄積されると表示されます。")

         # ── クイックフィルタ（強化版） ──
        st.markdown('<div class="section-title">クイックフィルタ</div>', unsafe_allow_html=True)
        
        filters = ["全台", "前日凹み", "前日プラス", "直近3日好調", "直近7日好調", "ジャグラー", "⭐星印"]
        fcols = st.columns(len(filters))
        
        for i, f in enumerate(filters):
            if fcols[i].button(f, key=f"qf_{f}"):
                st.session_state.active_filter = f
                st.rerun()

        af = st.session_state.active_filter

        # === ここからフィルタ適用ロジック ===
        if af == "全台":
            df_display = df.dropna(subset=["前日差枚"]).sort_values("前日差枚", ascending=False)
        elif af == "前日凹み":
            df_display = df[df["前日差枚"] < 0].sort_values("前日差枚")
        elif af == "前日プラス":
            df_display = df[df["前日差枚"] > 0].sort_values("前日差枚", ascending=False)
        elif af == "直近3日好調":
            if 'summary_df' in locals() and not summary_df.empty:
                temp = summary_df.nlargest(50, "直近3日合計").copy()   # 上位50台まで
                df_display = temp.merge(df[["台番", "機種名", "前日差枚", "スコア", "is_juggler"]], 
                                      on="台番", how="left")
            else:
                df_display = df.dropna(subset=["前日差枚"]).sort_values("前日差枚", ascending=False)
        elif af == "直近7日好調":
            if 'summary_df' in locals() and not summary_df.empty:
                temp = summary_df.nlargest(50, "直近7日合計").copy()
                df_display = temp.merge(df[["台番", "機種名", "前日差枚", "スコア", "is_juggler"]], 
                                      on="台番", how="left")
            else:
                df_display = df.dropna(subset=["前日差枚"]).sort_values("前日差枚", ascending=False)
        elif af == "ジャグラー":
            df_display = df[df["is_juggler"]].sort_values("前日差枚", ascending=False)
        elif af == "⭐星印":
            starred = [k for k, v in st.session_state.stars.items() if v]
            df_display = df[df["台番"].apply(lambda x: str(int(x)) if not np.isnan(x) else "").isin(starred)]
            df_display = df_display.sort_values("前日差枚", ascending=False)
        else:
            df_display = df.dropna(subset=["前日差枚"]).sort_values("前日差枚", ascending=False)

        # フィルタ結果の件数表示
        st.markdown(f'<div style="font-size:0.8rem;color:#7a8aaa;margin-bottom:0.6rem;">表示中: {len(df_display)} 台</div>', unsafe_allow_html=True)

        # ── おすすめカード（df_display ではなく全台から抽出のままでもOK） ──
        st.markdown('<div class="section-title">⭐ おすすめ台</div>', unsafe_allow_html=True)
        card_df = pd.concat([df.nlargest(3,"前日差枚"), df.nsmallest(2,"前日差枚")]).drop_duplicates()
        # （おすすめカード部分は変更なし・元のコードのまま）

        # おすすめカード（そのまま）
        st.markdown('<div class="section-title">⭐ おすすめ台</div>', unsafe_allow_html=True)
        card_df = pd.concat([df.nlargest(3,"前日差枚"), df.nsmallest(2,"前日差枚")]).drop_duplicates()
        for idx, row in card_df.iterrows():
            diff = row["前日差枚"]
            score = row["スコア"]
            sc = score_color(score)
            dc = diff_class(diff)
            is_hot = diff > 0 if not np.isnan(diff) else True
            台番_str = str(int(row["台番"])) if not np.isnan(row["台番"]) else "?"
            is_starred = st.session_state.stars.get(台番_str, False)
            badges = ""
            if not np.isnan(diff):
                if diff > 2000: badges += '<span class="badge badge-hot">🔥 好調</span>'
                elif diff < -2000: badges += '<span class="badge badge-cold">❄ 凹み狙い</span>'
            if is_starred: badges += '<span class="badge badge-star">⭐ 注目</span>'
            if row["is_juggler"]: badges += '<span class="badge badge-juggler">🎰 ジャグ</span>'
            
            st.markdown(f"""<div class="card {'card-hot' if is_hot else 'card-cold'}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div><div class="machine-num">台番 {台番_str}</div>
                <div class="machine-name">{row['機種名']}</div><div>{badges}</div></div>
                <div style="text-align:right;"><div class="{dc}">{diff_sign(diff)}</div>
                <div style="font-size:0.65rem;color:#7a8aaa;">週平均 {diff_sign(row['週平均'])}</div></div>
              </div>
              <div style="margin-top:6px;">
                <div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#7a8aaa;margin-bottom:2px;">
                  <span>スコア</span><span style="color:{sc};">{score:.0f}/100</span></div>
                <div class="score-bar-wrap"><div class="score-bar-fill" style="width:{score}%;background:linear-gradient(90deg,{sc}88,{sc});"></div></div>
              </div></div>""", unsafe_allow_html=True)
            
            btn_c1, btn_c2 = st.columns([1,3])
            with btn_c1:
                star_icon = "⭐" if is_starred else "☆"
                if st.button(f"{star_icon} 星", key=f"star_home_{idx}"):
                    st.session_state.stars[台番_str] = not is_starred
                    st.rerun()
            with btn_c2:
                memo = st.session_state.memos.get(台番_str, "")
                if memo: 
                    st.markdown(f'<div class="memo-box">📝 {memo}</div>', unsafe_allow_html=True)

        # ランキング（そのまま）
        st.markdown('<div class="section-title">📊 差枚ランキング</div>', unsafe_allow_html=True)
        ct, cb = st.columns(2)
        with ct:
            st.markdown('<div style="font-size:0.75rem;color:#00ff88;margin-bottom:4px;">▲ TOP 5</div>', unsafe_allow_html=True)
            top5 = df.nlargest(5,"前日差枚")[["台番","機種名","前日差枚"]].copy()
            top5["台番"] = top5["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            top5["前日差枚"] = top5["前日差枚"].apply(diff_sign)
            st.dataframe(top5, hide_index=True, use_container_width=True, height=210)
        with cb:
            st.markdown('<div style="font-size:0.75rem;color:#ff4444;margin-bottom:4px;">▼ WORST 5</div>', unsafe_allow_html=True)
            bot5 = df.nsmallest(5,"前日差枚")[["台番","機種名","前日差枚"]].copy()
            bot5["台番"] = bot5["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            bot5["前日差枚"] = bot5["前日差枚"].apply(diff_sign)
            st.dataframe(bot5, hide_index=True, use_container_width=True, height=210)

# ════════════════════════════════════════════
# 🔔 アラートタブ
# ════════════════════════════════════════════
with tab_alert:
    df = st.session_state.df_main
    if df is None:
        st.info("データを読み込み中です...")
    else:
        history, date_labels = load_history()
        alerts, _ = calc_alerts(df, history, st.session_state.stars)

        days_count = len(date_labels)
        st.markdown(f'<div style="font-size:0.75rem;color:#7a8aaa;margin-bottom:0.8rem;">蓄積データ: <span style="color:#00ffcc;">{days_count}日分</span> | {", ".join(date_labels[-3:]) if date_labels else "なし"}</div>', unsafe_allow_html=True)

        if days_count < 3:
            st.info("💡 アラートはデータが3日以上蓄積されると精度が上がります。現在は前日データのみで判定しています。")

        if not alerts:
            st.markdown('<div style="color:#7a8aaa;font-size:0.9rem;text-align:center;padding:2rem;">現在アラートはありません</div>', unsafe_allow_html=True)
        else:
            # タイプ別に分類
            danger_alerts = [a for a in alerts if a["type"]=="danger"]
            cold_alerts = [a for a in alerts if a["type"]=="cold"]
            hot_alerts = [a for a in alerts if a["type"]=="hot"]
            star_alerts = [a for a in alerts if a["type"]=="star"]

            if danger_alerts:
                st.markdown('<div class="section-title">⚠️ 大幅凹み</div>', unsafe_allow_html=True)
                for a in danger_alerts[:5]:
                    st.markdown(f"""<div class="alert-card">
                      <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div><div class="machine-num">{a['icon']} {a['label']} | 台番 {a['台番']}</div>
                        <div class="machine-name" style="font-size:0.9rem;">{a['機種名']}</div>
                        <div style="font-size:0.7rem;color:#7a8aaa;">{a['detail']}</div></div>
                        <div class="diff-minus">{diff_sign(a['diff'])}</div>
                      </div></div>""", unsafe_allow_html=True)

            if cold_alerts:
                st.markdown('<div class="section-title">❄️ 連続凹み（狙い目候補）</div>', unsafe_allow_html=True)
                for a in cold_alerts[:5]:
                    st.markdown(f"""<div class="alert-card">
                      <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div><div class="machine-num">{a['icon']} {a['label']} | 台番 {a['台番']}</div>
                        <div class="machine-name" style="font-size:0.9rem;">{a['機種名']}</div>
                        <div style="font-size:0.7rem;color:#7a8aaa;">{a['detail']}</div></div>
                        <div class="diff-minus">{diff_sign(a['diff'])}</div>
                      </div></div>""", unsafe_allow_html=True)

            if hot_alerts:
                st.markdown('<div class="section-title">🔥 連続好調</div>', unsafe_allow_html=True)
                for a in hot_alerts[:5]:
                    st.markdown(f"""<div class="alert-card-green">
                      <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div><div class="machine-num">{a['icon']} {a['label']} | 台番 {a['台番']}</div>
                        <div class="machine-name" style="font-size:0.9rem;">{a['機種名']}</div>
                        <div style="font-size:0.7rem;color:#7a8aaa;">{a['detail']}</div></div>
                        <div class="diff-plus">{diff_sign(a['diff'])}</div>
                      </div></div>""", unsafe_allow_html=True)

            if star_alerts:
                st.markdown('<div class="section-title">⭐ 注目台の変動</div>', unsafe_allow_html=True)
                for a in star_alerts:
                    st.markdown(f"""<div class="alert-card-star">
                      <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div><div class="machine-num">{a['icon']} {a['label']} | 台番 {a['台番']}</div>
                        <div class="machine-name" style="font-size:0.9rem;">{a['機種名']}</div>
                        <div style="font-size:0.7rem;color:#7a8aaa;">{a['detail']}</div></div>
                        <div class="{diff_class(a['diff'])}">{diff_sign(a['diff'])}</div>
                      </div></div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════
# 🎯 据え置き判別タブ
# ════════════════════════════════════════════
with tab_hold:
    df = st.session_state.df_main
    if df is None:
        st.info("データを読み込み中です...")
    else:
        history, date_labels = load_history()
        _, hold_candidates = calc_alerts(df, history, st.session_state.stars)

        st.markdown('<div class="section-title">🎯 高設定据え置き候補</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.75rem;color:#7a8aaa;margin-bottom:0.8rem;">連続プラス・高回転数・週平均から算出。データが蓄積されるほど精度が上がります。</div>', unsafe_allow_html=True)

        if not hold_candidates:
            st.markdown('<div style="color:#7a8aaa;font-size:0.9rem;text-align:center;padding:2rem;">据え置き候補なし（データ蓄積待ち）</div>', unsafe_allow_html=True)
        else:
            for h in hold_candidates:
                score = h["据え置きスコア"]
                sc = score_color(score)
                diff = h["diff"]
                st.markdown(f"""<div class="alert-card-blue">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                      <div class="machine-num">🎯 据え置きスコア | 台番 {h['台番']}</div>
                      <div class="machine-name" style="font-size:0.9rem;">{h['機種名']}</div>
                      <div style="font-size:0.7rem;color:#7a8aaa;">
                        連続プラス {h['連続プラス日']}日 | 週平均 {diff_sign(h['週平均'])}
                      </div>
                    </div>
                    <div style="text-align:right;">
                      <div class="hold-score">{score:.0f}<span style="font-size:0.7rem;color:#7a8aaa;">/100</span></div>
                      <div class="{diff_class(diff)}" style="font-size:1rem;">{diff_sign(diff)}</div>
                    </div>
                  </div>
                  <div class="score-bar-wrap" style="margin-top:6px;">
                    <div class="score-bar-fill" style="width:{score}%;background:linear-gradient(90deg,{sc}88,{sc});"></div>
                  </div></div>""", unsafe_allow_html=True)

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

        # カラー凡例
        st.markdown("""<div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:0.6rem;font-size:0.68rem;">
          <span style="background:#fff;color:#CC0000;border:1.5px solid #CC0000;padding:2px 5px;border-radius:3px;font-weight:bold;">-500↓</span>
          <span style="background:#fff;color:#333;border:1px solid #ccc;padding:2px 5px;border-radius:3px;">〜-1</span>
          <span style="background:#f0f0f0;color:#999;border:1px solid #ccc;padding:2px 5px;border-radius:3px;">0</span>
          <span style="background:#88CCEE;color:#333;padding:2px 5px;border-radius:3px;">+1〜</span>
          <span style="background:#DDDD00;color:#333;padding:2px 5px;border-radius:3px;">+1000〜</span>
          <span style="background:#66BB44;color:#fff;padding:2px 5px;border-radius:3px;">+2000〜</span>
          <span style="background:#CC44CC;color:#fff;padding:2px 5px;border-radius:3px;">+3000〜</span>
          <span style="background:#CC0000;color:#fff;padding:2px 5px;border-radius:3px;">+4000〜</span>
          <span style="background:#8B0000;color:#fff;padding:2px 5px;border-radius:3px;">+5000〜</span>
          <span style="background:#111;color:#FF4444;padding:2px 5px;border-radius:3px;">+10000↑</span>
          <span style="background:#0a0e1a;color:#FFD700;border:2px solid #FFD700;padding:2px 5px;border-radius:3px;">🎯狙い台</span>
        </div>""", unsafe_allow_html=True)

        # 島選択
        island_names = ["全島表示"] + [isl["name"] for isl in islands]
        sel_island = st.selectbox("島を選択", island_names)
        display_islands = [islands[island_names.index(sel_island)-1]] if sel_island != "全島表示" else islands

        # 狙い台セット（星印台を自動反映）
        target_machines = set()
        for k, v in st.session_state.stars.items():
            if v:
                try: target_machines.add(int(k))
                except: pass

        # ── 期間切り替えボタン ──
        st.markdown('<div style="font-size:0.75rem;color:#7a8aaa;margin-bottom:0.4rem;">表示期間を選択</div>', unsafe_allow_html=True)
        period_cols = st.columns(3)
        if "island_period" not in st.session_state:
            st.session_state.island_period = "前日"
        with period_cols[0]:
            if st.button("📅 前日", use_container_width=True, key="period_1d"):
                st.session_state.island_period = "前日"
        with period_cols[1]:
            if st.button("📅 直近3日", use_container_width=True, key="period_3d"):
                st.session_state.island_period = "直近3日"
        with period_cols[2]:
            if st.button("📅 直近7日", use_container_width=True, key="period_7d"):
                st.session_state.island_period = "直近7日"

        period = st.session_state.island_period
        st.markdown(f'<div style="font-size:0.7rem;color:#00ffcc;margin-bottom:0.6rem;">表示中: <b>{period}</b>の合計差枚</div>', unsafe_allow_html=True)

        # 期間に応じた集計
        diff_override = None
        if period != "前日":
            history, _ = load_history()
            if history:
                days = 3 if period == "直近3日" else 7
                diff_override = {}
                for num, date_dict in history.items():
                    sorted_dates = sorted(date_dict.keys())
                    recent = sorted_dates[-days:]
                    vals = [date_dict[d]["diff"] for d in recent
                            if not np.isnan(date_dict[d]["diff"])]
                    if vals:
                        diff_override[num] = sum(vals)
            else:
                st.info("履歴データがまだありません。前日データで表示します。")

        # 島図描画
        with st.spinner("島図描画中..."):
            fig_map = make_island_map(df, display_islands, target_machines=target_machines, diff_override=diff_override)
            st.plotly_chart(fig_map, use_container_width=True, config={
                "displayModeBar": True, "displaylogo": False, "scrollZoom": True,
                "modeBarButtonsToRemove": ["lasso2d","select2d"],
            })

        # ── 狙い台登録エリア ──
        st.markdown('<div class="section-title">🎯 狙い台登録</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.75rem;color:#7a8aaa;margin-bottom:0.6rem;">台番を入力して狙い台に登録。島図上で金色枠で表示されます。</div>', unsafe_allow_html=True)

        # 島が選択されている場合は台番リストを表示
        if sel_island != "全島表示":
            isl = islands[island_names.index(sel_island)-1]
            all_machines = [m for col in isl["rows"] for m in col]
            island_df = df[df["台番"].apply(lambda x: int(x) if not np.isnan(x) else -1).isin(all_machines)].copy()

            if not island_df.empty:
                island_df = island_df.sort_values("前日差枚", ascending=False)

                st.markdown('<div style="font-size:0.75rem;color:#00ffcc;margin-bottom:0.4rem;">この島の台一覧（タップで狙い台登録）</div>', unsafe_allow_html=True)

                # 台ごとにボタン表示（5列）
                machine_list = island_df[["台番","機種名","前日差枚"]].values.tolist()
                cols_per_row = 3
                for i in range(0, len(machine_list), cols_per_row):
                    row_machines = machine_list[i:i+cols_per_row]
                    btn_cols = st.columns(cols_per_row)
                    for j, (台番_f, 機種, diff_v) in enumerate(row_machines):
                        台番_n = int(台番_f) if not np.isnan(台番_f) else None
                        if 台番_n is None: continue
                        台番_str = str(台番_n)
                        is_starred = st.session_state.stars.get(台番_str, False)
                        diff_display = diff_sign(diff_v) if not np.isnan(diff_v) else "?"
                        # 色
                        if not np.isnan(diff_v) and diff_v >= 1000:
                            btn_style = "color:#003820;"
                        elif not np.isnan(diff_v) and diff_v <= -500:
                            btn_style = "color:#CC0000;"
                        else:
                            btn_style = ""
                        star_mark = "🎯" if is_starred else ""
                        label = f"{star_mark}#{台番_n} {diff_display}"
                        with btn_cols[j]:
                            if st.button(label, key=f"island_btn_{台番_n}", use_container_width=True):
                                st.session_state.stars[台番_str] = not is_starred
                                st.rerun()

        # 手動入力エリア
        st.markdown('<div style="margin-top:0.8rem;"></div>', unsafe_allow_html=True)
        inp_col1, inp_col2 = st.columns([2,1])
        with inp_col1:
            manual_input = st.text_input("台番を直接入力", placeholder="例: 1147", key="island_manual_input")
        with inp_col2:
            st.markdown("<div style='margin-top:1.6rem;'></div>", unsafe_allow_html=True)
            if st.button("🎯 登録", use_container_width=True, key="island_manual_btn"):
                try:
                    num = int(manual_input.strip())
                    台番_str = str(num)
                    st.session_state.stars[台番_str] = True
                    st.success(f"台番 {num} を狙い台に登録しました！")
                    st.rerun()
                except:
                    st.error("正しい台番を入力してください")

        # 現在の狙い台一覧
        current_targets = [(k, v) for k, v in st.session_state.stars.items() if v]
        if current_targets:
            st.markdown('<div class="section-title">🎯 現在の狙い台</div>', unsafe_allow_html=True)
            target_cols = st.columns(4)
            for i, (台番_str, _) in enumerate(current_targets):
                matched = df[df["台番"].apply(lambda x: str(int(x)) if not np.isnan(x) else "") == 台番_str]
                diff = matched.iloc[0]["前日差枚"] if len(matched) > 0 else np.nan
                機種 = matched.iloc[0]["機種名"] if len(matched) > 0 else "?"
                with target_cols[i % 4]:
                    st.markdown(f"""<div style="background:#111828;border:1.5px solid #FFD700;border-radius:8px;padding:6px;text-align:center;margin-bottom:6px;">
                      <div style="font-size:0.65rem;color:#FFD700;">🎯 #{台番_str}</div>
                      <div style="font-size:0.7rem;color:#c8d8f0;">{機種[:6]}</div>
                      <div style="font-family:'Orbitron',monospace;font-size:0.8rem;color:{'#00ff88' if not np.isnan(diff) and diff>=0 else '#ff4444'};">{diff_sign(diff)}</div>
                    </div>""", unsafe_allow_html=True)
                    if st.button("✕", key=f"remove_target_{台番_str}", use_container_width=True):
                        st.session_state.stars[台番_str] = False
                        st.rerun()

# ════════════════════════════════════════════
# 📈 トレンドタブ
# ════════════════════════════════════════════
with tab_trend:
    df = st.session_state.df_main
    if df is None:
        st.info("データを読み込み中です...")
    else:
        history, date_labels = load_history()
        machine_options = df.apply(lambda r: f"#{int(r['台番']) if not np.isnan(r['台番']) else '?'} {r['機種名']}", axis=1).tolist()
        selected = st.multiselect("台を選択（最大6台）", options=machine_options,
            default=machine_options[:3] if len(machine_options)>=3 else machine_options, max_selections=6)

        if selected and history:
            sel_idx = [machine_options.index(l) for l in selected]
            df_sel = df.iloc[sel_idx]
            colors = ["#00ffcc","#00ff88","#ff8844","#aa88ff","#ff4488","#44aaff"]
            fig = go.Figure()

            for i, (_, row) in enumerate(df_sel.iterrows()):
                num = int(row["台番"]) if not np.isnan(row["台番"]) else None
                if not num or num not in history: continue
                mh = history[num]
                sorted_d = sorted(mh.keys())
                vals = [mh[d]["diff"] for d in sorted_d]
                color = colors[i % len(colors)]
                label = f"#{num} {row['機種名']}"
                fig.add_trace(go.Scatter(x=sorted_d, y=vals, mode="lines+markers",
                    name=label, line=dict(color=color, width=2.5), marker=dict(size=6, color=color)))
                if len(vals) >= 3:
                    ma = pd.Series(vals).rolling(3).mean()
                    fig.add_trace(go.Scatter(x=sorted_d, y=ma.values, mode="lines",
                        line=dict(color=color, width=1, dash="dot"), opacity=0.5, showlegend=False))

            fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.15)")
            fig.update_layout(height=320, paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1520",
                font=dict(family="Noto Sans JP", color="#a0b0cc", size=11),
                legend=dict(bgcolor="#111828", bordercolor="#1e2d45", borderwidth=1,
                           font=dict(size=10), orientation="h", y=-0.25),
                xaxis=dict(showgrid=True, gridcolor="#1e2d45"),
                yaxis=dict(showgrid=True, gridcolor="#1e2d45", title="差枚数"),
                margin=dict(l=50,r=10,t=20,b=70), hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        elif not history:
            st.info("履歴データがまだ蓄積されていません。数日後にお試しください。")

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
        c1,c2 = st.columns(2)
        min_d = c1.number_input("差枚 下限", value=-9999, step=500)
        max_d = c2.number_input("差枚 上限", value=9999, step=500)
        sort_by = st.selectbox("ソート", ["前日差枚","スコア","週平均","台番"])
        asc = st.checkbox("昇順", value=False)

        df_v = df.copy()
        if sel_m != "全機種": df_v = df_v[df_v["機種名"]==sel_m]
        df_v = df_v[df_v["前日差枚"].between(min_d, max_d, inclusive="both")]
        df_v = df_v.sort_values(sort_by, ascending=asc, na_position="last")

        st.markdown(f'<div style="font-size:0.75rem;color:#7a8aaa;margin:0.3rem 0;">{len(df_v)} 台表示中</div>', unsafe_allow_html=True)
        disp = df_v[["台番","機種名","前日差枚","週平均","スコア","回転数"]].copy()
        disp["台番"] = disp["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
        disp["前日差枚"] = disp["前日差枚"].apply(diff_sign)
        disp["週平均"] = disp["週平均"].apply(diff_sign)
        disp["スコア"] = disp["スコア"].apply(lambda x: f"{x:.0f}")
        disp["回転数"] = disp["回転数"].apply(lambda x: f"{int(x):,}" if not np.isnan(x) else "-")
        st.dataframe(disp, hide_index=True, use_container_width=True, height=400)

        vals = df_v["前日差枚"].dropna()
        if len(vals) > 0:
            fig_h = go.Figure(go.Histogram(x=vals, nbinsx=20,
                marker_color=["#00ff88" if v>=0 else "#ff4444" for v in vals], opacity=0.8))
            fig_h.add_vline(x=0, line_dash="dash", line_color="rgba(255,255,255,0.25)")
            fig_h.update_layout(height=180, paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1520",
                margin=dict(l=40,r=10,t=10,b=30),
                xaxis=dict(gridcolor="#1e2d45", tickfont=dict(size=9, color="#7a8aaa")),
                yaxis=dict(gridcolor="#1e2d45", tickfont=dict(size=9, color="#7a8aaa")),
                showlegend=False, bargap=0.1)
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar":False})

# ════════════════════════════════════════════
# ⭐ メモタブ
# ════════════════════════════════════════════
with tab_memo:
    df = st.session_state.df_main
    if df is None:
        st.info("データを読み込み中です...")
    else:
        machine_options = df.apply(lambda r: f"#{int(r['台番']) if not np.isnan(r['台番']) else '?'} {r['機種名']}", axis=1).tolist()
        sel_machine = st.selectbox("台を選択", machine_options)
        row = df.iloc[machine_options.index(sel_machine)]
        台番_str = str(int(row["台番"])) if not np.isnan(row["台番"]) else "?"
        is_starred = st.session_state.stars.get(台番_str, False)

        if st.button("⭐ 星印ON" if is_starred else "☆ 星印OFF", use_container_width=True):
            st.session_state.stars[台番_str] = not is_starred; st.rerun()

        new_memo = st.text_area("メモ", value=st.session_state.memos.get(台番_str,""), height=100)
        if st.button("💾 メモを保存", use_container_width=True):
            st.session_state.memos[台番_str] = new_memo; st.success("保存しました")

        st.markdown('<div class="section-title">星印一覧</div>', unsafe_allow_html=True)
        starred_list = [(k,v) for k,v in st.session_state.stars.items() if v]
        if starred_list:
            for 台番_s, _ in starred_list:
                matched = df[df["台番"].apply(lambda x: str(int(x)) if not np.isnan(x) else "")==台番_s]
                機種 = matched.iloc[0]["機種名"] if len(matched)>0 else "?"
                diff = matched.iloc[0]["前日差枚"] if len(matched)>0 else np.nan
                memo = st.session_state.memos.get(台番_s,"")
                st.markdown(f"""<div class="card">
                  <div style="display:flex;justify-content:space-between;">
                    <div><div class="machine-num">⭐ 台番 {台番_s}</div><div class="machine-name">{機種}</div></div>
                    <div class="{diff_class(diff)}">{diff_sign(diff)}</div>
                  </div>{'<div class="memo-box">📝 '+memo+'</div>' if memo else ''}</div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#7a8aaa;font-size:0.8rem;">星印をつけた台はまだありません</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════
# ⚙ 島設定タブ
# ════════════════════════════════════════════
with tab_island_edit:
    st.markdown('<div class="section-title">島の設定</div>', unsafe_allow_html=True)
    if st.button("➕ 島を追加", use_container_width=True):
        st.session_state.islands.append({"name":f"新しい島{len(st.session_state.islands)+1}","rows":[[]]})
        st.rerun()

    for i, island in enumerate(st.session_state.islands):
        with st.expander(f"✏️ {island['name']}", expanded=False):
            new_name = st.text_input("島名", value=island["name"], key=f"iname_{i}")
            st.session_state.islands[i]["name"] = new_name
            all_m = [str(m) for col in island["rows"] for m in col]
            machines_str = st.text_area("台番（カンマ区切り）", value=", ".join(all_m), height=80, key=f"imachines_{i}")
            cols_count = st.number_input("列数", min_value=1, max_value=20, value=len(island["rows"]), key=f"icols_{i}")
            if st.button("💾 保存", key=f"isave_{i}", use_container_width=True):
                try:
                    nums = [int(x.strip()) for x in machines_str.split(",") if x.strip().isdigit()]
                    per_col = max(1, len(nums)//cols_count)
                    new_rows = []
                    for c in range(cols_count):
                        s = c * per_col
                        e = s + per_col if c < cols_count-1 else len(nums)
                        if s < len(nums): new_rows.append(nums[s:e])
                    st.session_state.islands[i]["rows"] = new_rows
                    st.success("✅ 保存しました"); st.rerun()
                except Exception as e:
                    st.error(f"エラー: {e}")
            if st.button("🗑 削除", key=f"idel_{i}", use_container_width=True):
                st.session_state.islands.pop(i); st.rerun()

    st.markdown("---")
    if st.button("🔄 デフォルト配置に戻す", use_container_width=True):
        st.session_state.islands = DEFAULT_ISLANDS; st.rerun()

st.markdown("""<div style="text-align:center;padding:1.5rem 0 0.5rem;font-size:0.65rem;color:#3a4a5a;">
  SLOTDASH v4 | スーパーコスモ堺専用 | 個人利用専用<br>
  ※ このアプリはギャンブルを推奨するものではありません</div>""", unsafe_allow_html=True)
