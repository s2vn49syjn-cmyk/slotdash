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

def parse_num(val):
    if val is None: return np.nan
    if isinstance(val, (int, float)):
        try:
            f = float(val)
            return f if not (f != f) else np.nan
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
    if np.isnan(val): return "#f0f0f0"
    if val >= 10000: return "#111111"
    if val >= 5000: return "#8B0000"
    if val >= 4000: return "#CC0000"
    if val >= 3000: return "#CC44CC"
    if val >= 2000: return "#66BB44"
    if val >= 1000: return "#DDDD00"
    if val >= 1: return "#88CCEE"
    if val == 0: return "#f0f0f0"
    if val >= -499: return "#ffffff"
    return "#ffffff"

def diff_to_text_color(val):
    if np.isnan(val): return "#999999"
    if val >= 10000: return "#FF4444"
    if val >= 5000: return "#ffffff"
    if val >= 4000: return "#ffffff"
    if val >= 3000: return "#ffffff"
    if val >= 2000: return "#ffffff"
    if val >= 1000: return "#333333"
    if val >= 1: return "#333333"
    if val == 0: return "#999999"
    if val >= -499: return "#333333"
    return "#CC0000"

def get_gspread_client():
    creds_dict = st.secrets["gcp_service_account"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_latest_sheet():
    try:
        client = get_gspread_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        all_ws = spreadsheet.worksheets()
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

@st.cache_data(ttl=180)
def load_history(max_days=10):
    try:
        client = get_gspread_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        all_ws = spreadsheet.worksheets()
        date_sheets = [ws for ws in all_ws if re.match(r"\d{4}-\d{2}-\d{2}", ws.title)]
        date_sheets = sorted(date_sheets, key=lambda w: w.title, reverse=True)[:max_days]
        history = {}
        date_labels = [ws.title for ws in date_sheets]
        for ws in date_sheets:
            try:
                data = ws.get_all_records()
                if not data: continue
                df = pd.DataFrame(data)
                cols = {c.strip(): c for c in df.columns}
                def fc(*keys):
                    for k in keys:
                        for c in cols:
                            if k in c: return cols[c]
                    return None
                台番col = fc("台番", "台no", "No")
                差枚col = fc("差枚", "前日差枚", "差枚数")
                回転col = fc("回転数", "回転", "G数", "ゲーム数")
                if not 台番col or not 差枚col: continue
                for _, row in df.iterrows():
                    try:
                        num = int(parse_num(row[台番col]))
                        diff = parse_num(row[差枚col])
                        rot = parse_num(row[回転col]) if 回転col else np.nan
                        if num not in history: history[num] = {}
                        history[num][ws.title] = {"diff": diff, "rot": rot}
                    except: continue
            except: continue
        return history, date_labels
    except Exception as e:
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
    if not 台番col or not 機種col: return None, None
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
        if len(diffs) >= 3 and all(d < 0 for d in diffs[-3:]):
            alerts.append({"type": "cold", "icon": "❄️", "label": f"連続凹み{sum(1 for d in diffs if d<0)}日",
                "台番": num, "機種名": 機種, "diff": today_diff, "detail": " / ".join([diff_sign(d) for d in diffs[-3:]])})
        elif len(diffs) >= 3 and all(d > 0 for d in diffs[-3:]):
            alerts.append({"type": "hot", "icon": "🔥", "label": f"連続好調{sum(1 for d in diffs if d>0)}日",
                "台番": num, "機種名": 機種, "diff": today_diff, "detail": " / ".join([diff_sign(d) for d in diffs[-3:]])})
        if not np.isnan(today_diff) and today_diff <= -3000:
            alerts.append({"type": "danger", "icon": "⚠️", "label": "大幅凹み",
                "台番": num, "機種名": 機種, "diff": today_diff, "detail": f"前日差枚 {diff_sign(today_diff)}"})
        if stars.get(台番_str) and len(diffs) >= 2:
            change = diffs[-1] - diffs[-2]
            if abs(change) >= 2000:
                direction = "急上昇" if change > 0 else "急落下"
                alerts.append({"type": "star", "icon": "⭐", "label": f"注目台が{direction}",
                    "台番": num, "機種名": 機種, "diff": today_diff, "detail": f"前日比 {diff_sign(change)}"})
        plus_days = sum(1 for d in diffs if d > 0)
        hold_score = min(100, plus_days * 15
            + (20 if rots and np.mean(rots) >= 7000 else 0)
            + (15 if diffs and np.mean(diffs) > 500 else 0)
            + (20 if not np.isnan(today_diff) and today_diff >= 2000 else 0))
        if hold_score >= 50:
            hold_candidates.append({"台番": num, "機種名": 機種, "据え置きスコア": hold_score,
                "diff": today_diff, "連続プラス日": plus_days, "週平均": np.mean(diffs) if diffs else np.nan})
    hold_candidates.sort(key=lambda x: x["据え置きスコア"], reverse=True)
    return alerts, hold_candidates[:10]

DEFAULT_ISLANDS = [
    {"name": "875〜955", "pos": (0, 0), "rows": [
        [911,912,913,914,915,916,917,918,919,920,921,922,923,924,925,926,927,928,929,930,931,932,933,934,935,936,937,938,939,940,941,942,943,944],
        [875,876,877,878,879,880,881,882,883,884,885,886,887,888,889,890,891,892,893,894,895,896,897,898,899,900,901,902,903,904,905,906,907,908,909,910],
        [945,946,947,948,949,950,951,952,953,954,955]]},
    {"name": "839〜874", "pos": (1, 0), "rows": [
        [841,842,843,844,845,846,847,848,849,850,851,852,853,854,855,856,857,858,859,860,861,862,863,864,865,866,867,868,869,870,871,872],
        [839,840], [873,874]]},
    {"name": "801〜838", "pos": (2, 0), "rows": [
        [801,802,803,804,805,806,807,808,809,810,811,812,813,814,815,816,817,818,819,820,821,822,823,824,825,826,827,828,829,830,831,832,833,834,835,836,837,838]]},
    {"name": "982〜1020", "pos": (3, 0), "rows": [
        [982,983,984,985,986,987,988,989], [1010,1011,1012,1013,1014,1015,1016,1017,1018,1019,1020]]},
    {"name": "990〜1009", "pos": (0, -1), "rows": [
        [990,991,992,993,994,995,996,997,998,999], [1000,1001,1002,1003,1004,1005,1006,1007,1008,1009]]},
    {"name": "1065〜1109", "pos": (1, -1), "rows": [
        [1065,1066,1067,1068,1069,1070,1071,1072,1073,1074,1075,1076],
        [1077,1078,1079,1080,1081,1082,1083,1084,1085,1086,1087,1088,1089],
        [1090,1091,1092,1093,1094,1095,1096,1097,1098,1099,1100],
        [1101,1102,1103,1104,1105,1106,1107,1108,1109]]},
    {"name": "1116〜1131", "pos": (0, -2), "rows": [
        [1116,1117,1118,1119,1120,1121,1122,1123,1124], [1125,1126,1127,1128,1129,1130,1131]]},
    {"name": "1110〜1149", "pos": (1, -2), "rows": [
        [1110,1111,1112,1113,1114,1115],
        [1132,1133,1134,1135,1136,1137,1138,1139,1140],
        [1141,1142,1143,1144,1145,1146,1147,1148,1149]]},
    {"name": "1200〜1212", "pos": (2, -2), "rows": [
        [1200,1201,1202,1203,1204,1205,1206], [1207,1208,1209,1210,1211,1212]]},
    {"name": "1150〜1199", "pos": (3, -1), "rows": [
        [1150,1151,1152,1153,1154,1155,1156,1157,1158,1159,1160],
        [1161,1162,1163,1164,1165,1166,1167,1168,1169,1170],
        [1171,1172,1173,1174,1175,1176,1177,1178,1179,1180],
        [1181,1182,1183,1184,1185,1186,1187,1188,1189,1190,1191],
        [1192,1193,1194,1195,1196,1197,1198,1199]]},
    {"name": "1213〜1232", "pos": (3, -2), "rows": [
        [1213,1214,1215,1216,1217,1218,1219,1220],
        [1221,1222,1223,1224,1225,1226,1227,1228,1229,1230,1231,1232]]},
    {"name": "1233〜1260", "pos": (2, -3), "rows": [
        [1233,1234,1235,1236,1237,1238,1239,1240],
        [1241,1242,1243,1244,1245,1246,1247,1248,1249,1250],
        [1251,1252,1253,1254,1255,1256,1257,1258,1259,1260]]},
    {"name": "1261〜1304", "pos": (0, -3), "rows": [
        [1261,1262,1263,1264,1265,1266,1267,1268,1269,1270],
        [1271,1272,1273,1274,1275,1276,1277,1278,1279,1280],
        [1281,1282,1283,1284,1285,1286,1287,1288,1289,1290],
        [1291,1292,1293,1294,1295,1296,1297,1298,1299,1300],
        [1301,1302,1303,1304]]},
]


# ── Excelから取得した正確な台番座標（行・列ともランク正規化）──
MACHINE_POSITIONS = {
    801: (96, 75),
    802: (93, 75),
    803: (90, 75),
    804: (87, 75),
    805: (84, 75),
    806: (82, 75),
    807: (79, 75),
    808: (76, 75),
    809: (73, 75),
    810: (70, 75),
    811: (67, 75),
    812: (64, 75),
    813: (61, 75),
    814: (58, 75),
    815: (55, 75),
    816: (52, 75),
    817: (50, 75),
    818: (48, 75),
    819: (46, 75),
    820: (40, 75),
    821: (37, 75),
    822: (35, 75),
    823: (34, 75),
    824: (32, 75),
    825: (29, 75),
    826: (26, 75),
    827: (23, 75),
    828: (21, 75),
    829: (18, 75),
    830: (15, 75),
    831: (12, 75),
    832: (10, 75),
    833: (7, 75),
    834: (4, 75),
    835: (3, 75),
    836: (2, 75),
    837: (1, 75),
    838: (0, 75),
    839: (1, 10),
    840: (2, 9),
    841: (3, 8),
    842: (4, 8),
    843: (7, 8),
    844: (10, 8),
    845: (12, 8),
    846: (15, 8),
    847: (18, 8),
    848: (21, 8),
    849: (23, 8),
    850: (26, 8),
    851: (29, 8),
    852: (32, 8),
    853: (34, 8),
    854: (35, 8),
    855: (37, 8),
    856: (40, 8),
    857: (46, 8),
    858: (48, 8),
    859: (50, 8),
    860: (52, 8),
    861: (55, 8),
    862: (58, 8),
    863: (61, 8),
    864: (64, 8),
    865: (67, 8),
    866: (70, 8),
    867: (73, 8),
    868: (76, 8),
    869: (79, 8),
    870: (82, 8),
    871: (84, 8),
    872: (87, 8),
    873: (90, 10),
    874: (93, 11),
    875: (93, 7),
    876: (90, 6),
    877: (87, 4),
    878: (84, 4),
    879: (82, 4),
    880: (79, 4),
    881: (76, 4),
    882: (73, 4),
    883: (70, 4),
    884: (67, 4),
    885: (64, 4),
    886: (61, 4),
    887: (58, 4),
    888: (55, 4),
    889: (52, 4),
    890: (50, 4),
    891: (48, 4),
    892: (46, 4),
    893: (40, 4),
    894: (37, 4),
    895: (35, 4),
    896: (34, 4),
    897: (32, 4),
    898: (29, 4),
    899: (26, 4),
    900: (23, 4),
    901: (21, 4),
    902: (18, 4),
    903: (15, 4),
    904: (12, 4),
    905: (10, 4),
    906: (7, 4),
    907: (4, 4),
    908: (3, 4),
    909: (2, 5),
    910: (1, 6),
    911: (1, 1),
    912: (2, 0),
    913: (3, 0),
    914: (4, 0),
    915: (7, 0),
    916: (10, 0),
    917: (12, 0),
    918: (15, 0),
    919: (18, 0),
    920: (21, 0),
    921: (23, 0),
    922: (26, 0),
    923: (29, 0),
    924: (32, 0),
    925: (34, 0),
    926: (35, 0),
    927: (37, 0),
    928: (40, 0),
    929: (46, 0),
    930: (48, 0),
    931: (50, 0),
    932: (52, 0),
    933: (55, 0),
    934: (58, 0),
    935: (61, 0),
    936: (64, 0),
    937: (67, 0),
    938: (70, 0),
    939: (73, 0),
    940: (76, 0),
    941: (79, 0),
    942: (82, 0),
    943: (84, 0),
    944: (87, 0),
    945: (90, 1),
    946: (93, 2),
    947: (96, 3),
    948: (100, 44),
    949: (99, 47),
    950: (98, 50),
    951: (96, 53),
    952: (94, 56),
    953: (92, 58),
    954: (90, 61),
    955: (88, 64),
    982: (80, 64),
    983: (82, 61),
    984: (83, 58),
    985: (85, 56),
    986: (87, 53),
    987: (89, 50),
    988: (91, 47),
    989: (93, 44),
    990: (97, 37),
    991: (97, 34),
    992: (97, 32),
    993: (96, 29),
    994: (95, 26),
    995: (94, 23),
    996: (92, 20),
    997: (90, 18),
    998: (88, 16),
    999: (86, 13),
    1000: (83, 13),
    1001: (85, 16),
    1002: (87, 18),
    1003: (89, 20),
    1004: (91, 23),
    1005: (92, 26),
    1006: (93, 29),
    1007: (94, 32),
    1008: (94, 34),
    1009: (94, 37),
    1010: (89, 44),
    1011: (87, 47),
    1012: (85, 50),
    1013: (83, 53),
    1014: (82, 56),
    1015: (80, 58),
    1016: (78, 61),
    1017: (74, 67),
    1018: (72, 69),
    1019: (70, 71),
    1020: (68, 73),
    1065: (61, 71),
    1066: (63, 69),
    1067: (65, 67),
    1068: (67, 64),
    1069: (69, 61),
    1070: (71, 58),
    1071: (73, 56),
    1072: (75, 53),
    1073: (77, 50),
    1074: (79, 47),
    1075: (81, 44),
    1076: (82, 41),
    1077: (85, 37),
    1078: (85, 34),
    1079: (85, 32),
    1080: (84, 29),
    1081: (77, 16),
    1082: (75, 13),
    1083: (72, 13),
    1084: (74, 16),
    1085: (76, 18),
    1086: (78, 20),
    1087: (81, 29),
    1088: (81, 32),
    1089: (80, 38),
    1090: (79, 41),
    1091: (78, 44),
    1092: (76, 47),
    1093: (74, 50),
    1094: (72, 53),
    1095: (69, 56),
    1096: (66, 58),
    1097: (64, 61),
    1098: (61, 64),
    1099: (58, 67),
    1100: (55, 69),
    1101: (48, 73),
    1102: (46, 74),
    1103: (40, 72),
    1104: (34, 70),
    1105: (32, 69),
    1106: (26, 66),
    1107: (23, 63),
    1108: (21, 60),
    1109: (18, 57),
    1110: (15, 55),
    1111: (12, 52),
    1112: (11, 49),
    1113: (10, 46),
    1114: (9, 43),
    1115: (8, 40),
    1116: (5, 31),
    1117: (5, 28),
    1118: (6, 25),
    1119: (7, 22),
    1120: (8, 19),
    1121: (9, 17),
    1122: (10, 15),
    1123: (11, 12),
    1124: (19, 12),
    1125: (18, 15),
    1126: (17, 17),
    1127: (16, 19),
    1128: (15, 22),
    1129: (14, 25),
    1130: (13, 28),
    1131: (13, 31),
    1132: (16, 40),
    1133: (17, 43),
    1134: (18, 46),
    1135: (19, 49),
    1136: (21, 52),
    1137: (23, 55),
    1138: (26, 57),
    1139: (29, 57),
    1140: (29, 60),
    1141: (32, 61),
    1142: (34, 62),
    1143: (35, 63),
    1144: (37, 64),
    1145: (40, 65),
    1146: (46, 68),
    1147: (48, 67),
    1148: (50, 65),
    1149: (52, 64),
    1151: (55, 61),
    1152: (57, 58),
    1153: (61, 56),
    1154: (63, 53),
    1155: (65, 50),
    1156: (67, 47),
    1157: (69, 44),
    1158: (70, 41),
    1159: (71, 38),
    1160: (72, 35),
    1161: (72, 32),
    1162: (72, 29),
    1163: (71, 26),
    1164: (70, 23),
    1165: (69, 20),
    1166: (67, 18),
    1167: (65, 16),
    1168: (63, 13),
    1169: (60, 13),
    1170: (62, 16),
    1171: (64, 18),
    1172: (66, 20),
    1173: (67, 23),
    1174: (68, 26),
    1175: (68, 29),
    1176: (69, 34),
    1177: (68, 37),
    1178: (67, 40),
    1179: (66, 43),
    1180: (64, 46),
    1181: (62, 49),
    1182: (60, 52),
    1183: (58, 55),
    1184: (55, 57),
    1185: (50, 62),
    1186: (48, 63),
    1187: (46, 64),
    1188: (40, 62),
    1189: (37, 61),
    1190: (35, 60),
    1191: (34, 59),
    1192: (32, 57),
    1193: (26, 54),
    1194: (23, 51),
    1195: (22, 48),
    1196: (20, 45),
    1197: (19, 42),
    1198: (18, 39),
    1199: (17, 36),
    1200: (16, 28),
    1201: (17, 25),
    1202: (18, 22),
    1203: (19, 19),
    1204: (20, 17),
    1205: (21, 15),
    1206: (22, 12),
    1207: (29, 15),
    1208: (28, 17),
    1209: (27, 19),
    1210: (26, 22),
    1211: (25, 25),
    1212: (24, 28),
    1213: (25, 36),
    1214: (26, 39),
    1215: (27, 42),
    1216: (28, 45),
    1217: (29, 48),
    1218: (29, 50),
    1219: (32, 49),
    1220: (34, 51),
    1221: (35, 52),
    1222: (37, 53),
    1223: (40, 54),
    1224: (46, 56),
    1225: (48, 55),
    1226: (50, 55),
    1227: (50, 52),
    1228: (52, 52),
    1229: (53, 49),
    1230: (55, 46),
    1231: (57, 43),
    1232: (58, 40),
    1233: (59, 37),
    1234: (60, 34),
    1235: (59, 26),
    1236: (58, 23),
    1237: (57, 20),
    1238: (55, 18),
    1239: (53, 16),
    1240: (51, 13),
    1241: (46, 14),
    1242: (48, 15),
    1243: (52, 18),
    1244: (54, 20),
    1245: (55, 23),
    1246: (56, 26),
    1247: (57, 29),
    1248: (57, 32),
    1249: (57, 34),
    1250: (56, 37),
    1251: (55, 40),
    1252: (54, 43),
    1253: (52, 46),
    1254: (48, 50),
    1255: (46, 51),
    1256: (40, 51),
    1257: (37, 50),
    1258: (34, 46),
    1259: (33, 43),
    1260: (32, 40),
    1261: (31, 37),
    1262: (30, 34),
    1263: (30, 32),
    1264: (30, 29),
    1265: (31, 26),
    1266: (32, 23),
    1267: (33, 20),
    1268: (34, 18),
    1269: (37, 15),
    1270: (40, 14),
    1271: (41, 20),
    1272: (40, 21),
    1273: (37, 25),
    1274: (36, 29),
    1275: (36, 32),
    1276: (36, 34),
    1277: (37, 37),
    1278: (37, 41),
    1279: (40, 42),
    1280: (41, 43),
    1281: (44, 43),
    1282: (46, 42),
    1283: (48, 42),
    1284: (49, 39),
    1285: (49, 36),
    1286: (50, 33),
    1287: (50, 30),
    1288: (49, 27),
    1289: (49, 24),
    1290: (48, 22),
    1291: (46, 21),
    1292: (44, 20),
    1293: (40, 37),
    1294: (39, 34),
    1295: (38, 32),
    1296: (39, 29),
    1297: (40, 26),
    1298: (42, 21),
    1299: (43, 21),
    1300: (45, 26),
    1301: (46, 29),
    1302: (47, 32),
    1303: (46, 34),
    1304: (45, 37),
}

def make_island_map(df, islands=None, target_machines=None, diff_override=None):
    """正規化済みExcel座標でPDF通りの島図を描画"""
    diff_map = {}
    for _, row in df.iterrows():
        if not np.isnan(row["台番"]):
            n = int(row["台番"])
            diff_map[n] = row["前日差枚"]
    if diff_override:
        for n, v in diff_override.items():
            diff_map[n] = v
    if target_machines is None:
        target_machines = set()

    # セルサイズ
    CW = 50   # セル幅
    CH = 36   # セル高
    PAD = 2

    shapes = []
    annotations = []

    for mno, (ex_row, ex_col) in MACHINE_POSITIONS.items():
        px = ex_col * CW
        py = -ex_row * CH  # y軸反転（上が小さい行番号）

        diff = diff_map.get(mno, np.nan)
        bg = diff_to_color(diff)
        text_c = diff_to_text_color(diff)
        is_target = mno in target_machines

        if np.isnan(diff):
            diff_text = "?"
        elif diff >= 0:
            diff_text = f"+{int(diff):,}"
        else:
            diff_text = f"{int(diff):,}"

        # 枠線色
        if is_target:
            border_c = "#ffffff"; border_w = 3
        elif not np.isnan(diff) and diff <= -500:
            border_c = "rgba(200,0,0,0.8)"; border_w = 1.5
        else:
            border_c = "rgba(80,80,80,0.5)"; border_w = 0.8

        # セル背景
        shapes.append(dict(type="rect",
            x0=px, y0=py - CH + PAD,
            x1=px + CW - PAD, y1=py,
            fillcolor=bg,
            line=dict(color=border_c, width=border_w),
            layer="below"))

        # 狙い台：金枠
        if is_target:
            shapes.append(dict(type="rect",
                x0=px - 3, y0=py - CH - 2,
                x1=px + CW + 2, y1=py + 3,
                fillcolor="rgba(0,0,0,0)",
                line=dict(color="#FFD700", width=2.5),
                layer="above"))
            annotations.append(dict(
                x=px + CW/2, y=py + 9,
                text="🎯", showarrow=False,
                font=dict(size=11), xanchor="center"))

        # 台番（上部）
        num_c = "#ffffff" if not np.isnan(diff) and diff >= 10000 else "rgba(0,0,0,0.6)"
        annotations.append(dict(
            x=px + CW/2, y=py - 8,
            text=str(mno),
            showarrow=False,
            font=dict(size=9, color=num_c),
            xanchor="center"))

        # 差枚（中央）
        annotations.append(dict(
            x=px + CW/2, y=py - CH/2 - 2,
            text=f"<b>{diff_text}</b>",
            showarrow=False,
            font=dict(size=10, color=text_c),
            xanchor="center"))

    # 全体サイズ
    all_px = [c * CW for _, (r, c) in MACHINE_POSITIONS.items()]
    all_py = [-r * CH for _, (r, c) in MACHINE_POSITIONS.items()]
    total_w = max(all_px) + CW * 3
    total_h = abs(min(all_py)) + CH * 3

    fig = go.Figure()
    fig.update_layout(
        width=max(1400, total_w),
        height=max(1200, total_h),
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0d1520",
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False, range=[-CW, total_w]),
        yaxis=dict(visible=False, range=[min(all_py) - CH*2, CH*2]),
        hovermode="closest",
    )
    fig.update_layout(shapes=shapes, annotations=annotations)
    return fig


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

tab_home, tab_alert, tab_hold, tab_island, tab_trend, tab_all, tab_memo, tab_island_edit = st.tabs([
    "🏠 ホーム", "🔔 アラート", "🎯 据え置き", "🗺 島図", "📈 トレンド", "📋 全台", "⭐ メモ", "⚙ 島設定"
])

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

        st.markdown('<div class="section-title">📅 直近傾向まとめ（朝イチ参考）</div>', unsafe_allow_html=True)
        history, date_labels = load_history()

        if history and len(date_labels) >= 3:
            summary_data = []
            for _, row in df.iterrows():
                if np.isnan(row["台番"]): continue
                num = int(row["台番"])
                machine_hist = history.get(num, {})
                sorted_dates = sorted(machine_hist.keys(), reverse=True)
                recent3 = sorted_dates[:3]
                sum3 = sum(machine_hist[d]["diff"] for d in recent3 if not np.isnan(machine_hist[d]["diff"]))
                recent7 = sorted_dates[:7]
                sum7 = sum(machine_hist[d]["diff"] for d in recent7 if not np.isnan(machine_hist[d]["diff"]))
                rots_recent = [machine_hist[d].get("rot", np.nan) for d in recent3]
                valid_rots = [r for r in rots_recent if not np.isnan(r)]
                high_rot_days = len([r for r in valid_rots if r >= 7000])
                avg_rot = round(np.mean(valid_rots)) if valid_rots else np.nan
                summary_data.append({
                    "台番": num, "機種名": row["機種名"],
                    "直近3日合計": sum3, "直近7日合計": sum7,
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
                st.info("直近3日間で高回転（7000G以上）が続いている台はまだありません。")
            if st.button("🌟 上位好調台をすべて星印に登録（3日+7日トップ各5台）", use_container_width=True):
                top_nums = set(summary_df.nlargest(5, "直近3日合計")["台番"]) | set(summary_df.nlargest(5, "直近7日合計")["台番"])
                for n in top_nums:
                    st.session_state.stars[str(int(n))] = True
                st.success(f"{len(top_nums)}台を星印に登録しました！")
                st.rerun()
        else:
            st.info("📅 直近傾向まとめは、3日以上の履歴データが蓄積されると表示されます。")
            summary_df = pd.DataFrame()

        st.markdown('<div class="section-title">クイックフィルタ</div>', unsafe_allow_html=True)
        filters = ["全台", "前日凹み", "前日プラス", "直近3日合計", "直近7日合計", "ジャグラー", "⭐星印"]
        fcols = st.columns(len(filters))
        for i, f in enumerate(filters):
            if fcols[i].button(f, key=f"qf_{f}"):
                st.session_state.active_filter = f
                st.rerun()

        af = st.session_state.active_filter
        if af == "全台":
            df_display = df.dropna(subset=["前日差枚"]).sort_values("前日差枚", ascending=False)
        elif af == "前日凹み":
            df_display = df[df["前日差枚"] < 0].sort_values("前日差枚")
        elif af == "前日プラス":
            df_display = df[df["前日差枚"] > 0].sort_values("前日差枚", ascending=False)
        elif af == "直近3日合計":
            if not summary_df.empty:
                temp = summary_df.nlargest(999, "直近3日合計").copy()
                df_display = temp.merge(df[["台番", "機種名", "前日差枚", "スコア", "is_juggler", "回転数"]], on="台番", how="left")
                df_display = df_display.sort_values("直近3日合計", ascending=False)
            else:
                df_display = df.dropna(subset=["前日差枚"]).sort_values("前日差枚", ascending=False)
        elif af == "直近7日合計":
            if not summary_df.empty:
                temp = summary_df.nlargest(999, "直近7日合計").copy()
                df_display = temp.merge(df[["台番", "機種名", "前日差枚", "スコア", "is_juggler", "回転数"]], on="台番", how="left")
                df_display = df_display.sort_values("直近7日合計", ascending=False)
            else:
                df_display = df.dropna(subset=["前日差枚"]).sort_values("前日差枚", ascending=False)
        elif af == "ジャグラー":
            df_display = df[df["is_juggler"]].sort_values("前日差枚", ascending=False)
        elif af == "⭐星印":
            starred = [k for k, v in st.session_state.stars.items() if v]
            df_display = df[df["台番"].apply(lambda x: str(int(x)) if not np.isnan(x) else "").isin(starred)]
            df_display = df_display.sort_values("前日差枚", ascending=False) if not df_display.empty else df.head(0)
        else:
            df_display = df.dropna(subset=["前日差枚"]).sort_values("前日差枚", ascending=False)

        st.markdown(f'<div style="font-size:0.82rem;color:#00ffcc;margin:0.4rem 0 0.8rem;">▶ フィルタ: {af}　表示台数: {len(df_display)} 台</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">⭐ おすすめ台</div>', unsafe_allow_html=True)
        if len(df_display) >= 5:
            card_df = pd.concat([df_display.nlargest(3, "前日差枚"), df_display.nsmallest(2, "前日差枚")]).drop_duplicates()
        else:
            card_df = pd.concat([df.nlargest(3, "前日差枚"), df.nsmallest(2, "前日差枚")]).drop_duplicates()

        for idx, row in card_df.iterrows():
            diff = row["前日差枚"]
            score = row.get("スコア", 50)
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
            if row.get("is_juggler", False): badges += '<span class="badge badge-juggler">🎰 ジャグ</span>'
            st.markdown(f"""<div class="card {'card-hot' if is_hot else 'card-cold'}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div><div class="machine-num">台番 {台番_str}</div>
                <div class="machine-name">{row['機種名']}</div><div>{badges}</div></div>
                <div style="text-align:right;"><div class="{dc}">{diff_sign(diff)}</div>
                <div style="font-size:0.65rem;color:#7a8aaa;">週平均 {diff_sign(row.get('週平均', np.nan))}</div></div>
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
                    st.session_state.stars[台番_str] = not is_starred; st.rerun()
            with btn_c2:
                memo = st.session_state.memos.get(台番_str, "")
                if memo: st.markdown(f'<div class="memo-box">📝 {memo}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">📊 差枚ランキング（現在のフィルタ）</div>', unsafe_allow_html=True)
        ct, cb = st.columns(2)
        with ct:
            st.markdown('<div style="font-size:0.75rem;color:#00ff88;margin-bottom:4px;">▲ TOP 5</div>', unsafe_allow_html=True)
            top5 = df_display.nlargest(5, "前日差枚")[["台番","機種名","前日差枚"]].copy()
            top5["台番"] = top5["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            top5["前日差枚"] = top5["前日差枚"].apply(diff_sign)
            st.dataframe(top5, hide_index=True, use_container_width=True, height=210)
        with cb:
            st.markdown('<div style="font-size:0.75rem;color:#ff4444;margin-bottom:4px;">▼ WORST 5</div>', unsafe_allow_html=True)
            bot5 = df_display.nsmallest(5, "前日差枚")[["台番","機種名","前日差枚"]].copy()
            bot5["台番"] = bot5["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            bot5["前日差枚"] = bot5["前日差枚"].apply(diff_sign)
            st.dataframe(bot5, hide_index=True, use_container_width=True, height=210)

        st.markdown('<div class="section-title">📋 全台一覧</div>', unsafe_allow_html=True)
        if af == "直近3日合計" and not summary_df.empty:
            disp = summary_df[["台番", "機種名", "直近3日合計", "前日差枚"]].copy()
            disp = disp.merge(df[["台番", "スコア"]], on="台番", how="left")
            disp = disp.sort_values("直近3日合計", ascending=False)
            disp["台番"] = disp["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            disp["直近3日合計"] = disp["直近3日合計"].apply(diff_sign)
            disp["前日差枚"] = disp["前日差枚"].apply(diff_sign)
            disp["スコア"] = disp["スコア"].apply(lambda x: f"{x:.0f}" if not np.isnan(x) else "-")
            column_order = ["台番", "機種名", "直近3日合計", "前日差枚", "スコア"]
        elif af == "直近7日合計" and not summary_df.empty:
            disp = summary_df[["台番", "機種名", "直近7日合計", "前日差枚"]].copy()
            disp = disp.merge(df[["台番", "スコア"]], on="台番", how="left")
            disp = disp.sort_values("直近7日合計", ascending=False)
            disp["台番"] = disp["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            disp["直近7日合計"] = disp["直近7日合計"].apply(diff_sign)
            disp["前日差枚"] = disp["前日差枚"].apply(diff_sign)
            disp["スコア"] = disp["スコア"].apply(lambda x: f"{x:.0f}" if not np.isnan(x) else "-")
            column_order = ["台番", "機種名", "直近7日合計", "前日差枚", "スコア"]
        else:
            disp = df_display[["台番", "機種名", "前日差枚", "スコア"]].copy()
            disp["台番"] = disp["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            disp["前日差枚"] = disp["前日差枚"].apply(diff_sign)
            disp["スコア"] = disp["スコア"].apply(lambda x: f"{x:.0f}" if not np.isnan(x) else "-")
            column_order = ["台番", "機種名", "前日差枚", "スコア"]
        st.dataframe(disp[column_order], hide_index=True, use_container_width=True, height=650)

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
            st.info("💡 アラートはデータが3日以上蓄積されると精度が上がります。")
        if not alerts:
            st.markdown('<div style="color:#7a8aaa;font-size:0.9rem;text-align:center;padding:2rem;">現在アラートはありません</div>', unsafe_allow_html=True)
        else:
            danger_alerts = [a for a in alerts if a["type"]=="danger"]
            cold_alerts = [a for a in alerts if a["type"]=="cold"]
            hot_alerts = [a for a in alerts if a["type"]=="hot"]
            star_alerts = [a for a in alerts if a["type"]=="star"]
            if danger_alerts:
                st.markdown('<div class="section-title">⚠️ 大幅凹み</div>', unsafe_allow_html=True)
                for a in danger_alerts[:5]:
                    st.markdown(f"""<div class="alert-card"><div style="display:flex;justify-content:space-between;align-items:center;">
                        <div><div class="machine-num">{a['icon']} {a['label']} | 台番 {a['台番']}</div>
                        <div class="machine-name" style="font-size:0.9rem;">{a['機種名']}</div>
                        <div style="font-size:0.7rem;color:#7a8aaa;">{a['detail']}</div></div>
                        <div class="diff-minus">{diff_sign(a['diff'])}</div></div></div>""", unsafe_allow_html=True)
            if cold_alerts:
                st.markdown('<div class="section-title">❄️ 連続凹み（狙い目候補）</div>', unsafe_allow_html=True)
                for a in cold_alerts[:5]:
                    st.markdown(f"""<div class="alert-card"><div style="display:flex;justify-content:space-between;align-items:center;">
                        <div><div class="machine-num">{a['icon']} {a['label']} | 台番 {a['台番']}</div>
                        <div class="machine-name" style="font-size:0.9rem;">{a['機種名']}</div>
                        <div style="font-size:0.7rem;color:#7a8aaa;">{a['detail']}</div></div>
                        <div class="diff-minus">{diff_sign(a['diff'])}</div></div></div>""", unsafe_allow_html=True)
            if hot_alerts:
                st.markdown('<div class="section-title">🔥 連続好調</div>', unsafe_allow_html=True)
                for a in hot_alerts[:5]:
                    st.markdown(f"""<div class="alert-card-green"><div style="display:flex;justify-content:space-between;align-items:center;">
                        <div><div class="machine-num">{a['icon']} {a['label']} | 台番 {a['台番']}</div>
                        <div class="machine-name" style="font-size:0.9rem;">{a['機種名']}</div>
                        <div style="font-size:0.7rem;color:#7a8aaa;">{a['detail']}</div></div>
                        <div class="diff-plus">{diff_sign(a['diff'])}</div></div></div>""", unsafe_allow_html=True)
            if star_alerts:
                st.markdown('<div class="section-title">⭐ 注目台の変動</div>', unsafe_allow_html=True)
                for a in star_alerts:
                    st.markdown(f"""<div class="alert-card-star"><div style="display:flex;justify-content:space-between;align-items:center;">
                        <div><div class="machine-num">{a['icon']} {a['label']} | 台番 {a['台番']}</div>
                        <div class="machine-name" style="font-size:0.9rem;">{a['機種名']}</div>
                        <div style="font-size:0.7rem;color:#7a8aaa;">{a['detail']}</div></div>
                        <div class="{diff_class(a['diff'])}">{diff_sign(a['diff'])}</div></div></div>""", unsafe_allow_html=True)

with tab_hold:
    df = st.session_state.df_main
    if df is None:
        st.info("データを読み込み中です...")
    else:
        history, date_labels = load_history()
        _, hold_candidates = calc_alerts(df, history, st.session_state.stars)
        st.markdown('<div class="section-title">🎯 高設定据え置き候補</div>', unsafe_allow_html=True)
        if not hold_candidates:
            st.markdown('<div style="color:#7a8aaa;font-size:0.9rem;text-align:center;padding:2rem;">据え置き候補なし（データ蓄積待ち）</div>', unsafe_allow_html=True)
        else:
            for h in hold_candidates:
                score = h["据え置きスコア"]
                sc = score_color(score)
                diff = h["diff"]
                st.markdown(f"""<div class="alert-card-blue">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div><div class="machine-num">🎯 据え置きスコア | 台番 {h['台番']}</div>
                    <div class="machine-name" style="font-size:0.9rem;">{h['機種名']}</div>
                    <div style="font-size:0.7rem;color:#7a8aaa;">連続プラス {h['連続プラス日']}日 | 週平均 {diff_sign(h['週平均'])}</div></div>
                    <div style="text-align:right;"><div class="hold-score">{score:.0f}<span style="font-size:0.7rem;color:#7a8aaa;">/100</span></div>
                    <div class="{diff_class(diff)}" style="font-size:1rem;">{diff_sign(diff)}</div></div>
                  </div>
                  <div class="score-bar-wrap" style="margin-top:6px;">
                    <div class="score-bar-fill" style="width:{score}%;background:linear-gradient(90deg,{sc}88,{sc});"></div>
                  </div></div>""", unsafe_allow_html=True)

with tab_island:
    df = st.session_state.df_main
    islands = st.session_state.islands
    if df is None:
        st.info("データを読み込み中です...")
    else:
        st.markdown('<div class="section-title">🗺 島図</div>', unsafe_allow_html=True)
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

        island_names = ["全島表示"] + [isl["name"] for isl in islands]
        sel_island = st.selectbox("島を選択", island_names)
        display_islands = [islands[island_names.index(sel_island)-1]] if sel_island != "全島表示" else islands

        target_machines = set()
        for k, v in st.session_state.stars.items():
            if v:
                try: target_machines.add(int(k))
                except: pass

        st.markdown(f'<div style="font-size:0.75rem;color:#ffd700;margin-bottom:0.4rem;">🎯 現在の狙い台: {len(target_machines)} 台</div>', unsafe_allow_html=True)

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
        st.markdown(f'<div style="font-size:0.7rem;color:#00ffcc;margin-bottom:0.6rem;">表示中: <b>{period}</b></div>', unsafe_allow_html=True)

        diff_override = None
        if period != "前日":
            history, _ = load_history()
            if history:
                days = 3 if period == "直近3日" else 7
                diff_override = {}
                for num, date_dict in history.items():
                    sorted_dates = sorted(date_dict.keys())
                    recent = sorted_dates[-days:]
                    vals = [date_dict[d]["diff"] for d in recent if not np.isnan(date_dict[d]["diff"])]
                    if vals:
                        diff_override[num] = sum(vals)

        with st.spinner("島図を描画中..."):
            fig_map = make_island_map(df, display_islands, target_machines=target_machines, diff_override=diff_override)
            st.plotly_chart(fig_map, use_container_width=True, config={
                "displayModeBar": True, "displaylogo": False, "scrollZoom": True,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"]
            })

        st.markdown('<div class="section-title">🎯 狙い台登録</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.75rem;color:#7a8aaa;margin-bottom:0.6rem;">台番を入力して狙い台に登録。島図上で金色枠で表示されます。</div>', unsafe_allow_html=True)

        if sel_island != "全島表示":
            isl = islands[island_names.index(sel_island)-1]
            all_machines = [m for col in isl["rows"] for m in col]
            island_df = df[df["台番"].apply(lambda x: int(x) if not np.isnan(x) else -1).isin(all_machines)].copy()
            if not island_df.empty:
                island_df = island_df.sort_values("前日差枚", ascending=False)
                st.markdown('<div style="font-size:0.75rem;color:#00ffcc;margin-bottom:0.4rem;">この島の台一覧（タップで狙い台登録）</div>', unsafe_allow_html=True)
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
                        star_mark = "🎯" if is_starred else ""
                        label = f"{star_mark}#{台番_n} {diff_display}"
                        with btn_cols[j]:
                            if st.button(label, key=f"island_btn_{台番_n}", use_container_width=True):
                                st.session_state.stars[台番_str] = not is_starred
                                st.rerun()

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
                legend=dict(bgcolor="#111828", bordercolor="#1e2d45", borderwidth=1, font=dict(size=10), orientation="h", y=-0.25),
                xaxis=dict(showgrid=True, gridcolor="#1e2d45"),
                yaxis=dict(showgrid=True, gridcolor="#1e2d45", title="差枚数"),
                margin=dict(l=50,r=10,t=20,b=70), hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        elif not history:
            st.info("履歴データがまだ蓄積されていません。")

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
