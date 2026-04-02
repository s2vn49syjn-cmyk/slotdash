"""
scraper_actions.py v3 - 差枚取得修正版
みんレポの差枚列を正確に取得
"""

import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

TARGET_URL = "https://min-repo.com/tag/%E3%82%B9%E3%83%BC%E3%83%91%E3%83%BC%E3%82%B3%E3%82%B9%E3%83%A2%E3%83%97%E3%83%AC%E3%83%9F%E3%82%A2%E3%83%A0%E5%A0%BA%E5%BA%97/"
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://min-repo.com/",
    "Upgrade-Insecure-Requests": "1",
}

def connect_spreadsheet():
    creds_json = os.environ.get("GCP_CREDENTIALS", "")
    if not creds_json:
        raise ValueError("GCP_CREDENTIALS環境変数が設定されていません")
    creds_dict = json.loads(creds_json)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)

def get_or_create_sheet(spreadsheet, sheet_name):
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)

def migrate_old_data(spreadsheet):
    try:
        old_sheet = spreadsheet.worksheet("スロデータ")
        data = old_sheet.get_all_values()
        if not data:
            return
        date_str = "2026-03-29"
        try:
            spreadsheet.worksheet(date_str)
            print(f"日付シート {date_str} は既に存在します")
        except gspread.WorksheetNotFound:
            new_sheet = spreadsheet.add_worksheet(title=date_str, rows=len(data)+10, cols=25)
            new_sheet.update(data)
            print(f"既存データを {date_str} シートに移行しました")
    except gspread.WorksheetNotFound:
        pass
    except Exception as e:
        print(f"移行エラー（続行）: {e}")

def parse_num(text):
    """数値文字列をfloatに変換（マイナス対応）"""
    if not text or str(text).strip() in ["-", "", "−", "ー", "None", "nan"]:
        return ""
    s = str(text).strip()
    # 全角数字・記号を半角に
    s = s.replace("，", ",").replace("＋", "+").replace("－", "-").replace("ー", "-").replace("−", "-")
    s = s.replace(",", "")
    m = re.search(r"[+-]?\d+\.?\d*", s)
    if m:
        val = float(m.group())
        # みんレポは差枚がマイナスの場合、赤色テキストで表示
        # spanのclassがminusやredの場合はマイナスにする
        return val
    return ""

def parse_cell(cell):
    """
    セルの数値を取得（みんレポのマイナス表示に完全対応）
    みんレポはマイナス差枚をCSSクラスやstyleで赤表示する
    """
    text = cell.get_text(strip=True)
    if not text or text in ["-", "−", "", "ー"]:
        return ""

    # ── マイナス判定（複数パターン対応）──
    is_negative = False

    # 1. spanのclassにminus/red/negativeなど
    for span in cell.find_all("span"):
        classes = " ".join(span.get("class", []))
        style = span.get("style", "")
        if any(c in classes for c in ["minus", "red", "negative", "m", "down", "lose"]):
            is_negative = True; break
        if "color:red" in style or "color:#e" in style or "color:#f" in style:
            is_negative = True; break

    # 2. tdのclassやstyle
    if not is_negative:
        td_classes = " ".join(cell.get("class", []))
        td_style = cell.get("style", "")
        if any(c in td_classes for c in ["minus", "red", "negative", "down", "lose"]):
            is_negative = True
        if "color:red" in td_style or "color:#e" in td_style:
            is_negative = True

    # 3. テキスト自体にマイナス符号がある（全角・半角）
    text_clean = text.strip()
    text_clean = text_clean.replace("，", ",").replace("＋", "+")
    text_clean = text_clean.replace("－", "-").replace("ー", "-").replace("−", "-")
    text_clean = text_clean.replace(",", "")

    if text_clean.startswith("-"):
        is_negative = True

    # 数値抽出
    m = re.search(r"[+-]?\d+\.?\d*", text_clean)
    if not m:
        return text

    val = float(m.group())

    # マイナス判定でプラス値ならマイナスにする
    if is_negative and val > 0:
        val = -val

    return val

def fetch_page(url, retries=5):
    for i in range(retries):
        try:
            session = requests.Session()
            # セッションごとにヘッダーをセット
            session.headers.update(HEADERS)
            res = session.get(url, timeout=30, allow_redirects=True)
            res.encoding = "utf-8"
            print(f"  ステータス: {res.status_code} ({url[:60]})")
            if res.status_code == 200:
                return res.text
            elif res.status_code == 403:
                print(f"  アクセス拒否(403) - {i+1}回目")
                time.sleep(10 * (i + 1))
            else:
                print(f"  エラー: {res.status_code}")
                time.sleep(5)
        except Exception as e:
            print(f"  リトライ {i+1}/{retries}: {e}")
            time.sleep(8)
    return None

def scrape_and_save(target_date=None):
    """
    target_date: 取得対象日付 (例: "2026-03-29")
                 Noneの場合は昨日のデータを取得
    """
    jst_now = datetime.utcnow() + timedelta(hours=9)

    if target_date:
        # 指定日付を使用
        target = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        # デフォルト：昨日
        target = jst_now - timedelta(days=1)

    date_str = target.strftime("%Y-%m-%d")
    date_display = target.strftime("%Y/%m/%d")

    print(f"=== スクレイピング開始: {jst_now.strftime('%Y-%m-%d %H:%M:%S')} JST ===")
    print(f"対象日付: {date_str}")

    print("Google Sheetsに接続中...")
    spreadsheet = connect_spreadsheet()
    migrate_old_data(spreadsheet)

    # タグページ取得
    print(f"アクセス中: {TARGET_URL}")
    html = fetch_page(TARGET_URL)
    if not html:
        print("タグページの取得失敗")
        return False

    soup = BeautifulSoup(html, "html.parser")
    table_wrap = soup.select_one("div.table_wrap")
    if not table_wrap:
        print("table_wrapが見つかりません")
        return False

    latest_link = table_wrap.select_one("a")
    if not latest_link:
        print("レポートリンクが見つかりません")
        return False

    latest_url = latest_link.get("href")
    print(f"最新レポートURL: {latest_url}")

    time.sleep(2)
    html2 = fetch_page(latest_url)
    if not html2:
        print("レポートページの取得失敗")
        return False

    soup2 = BeautifulSoup(html2, "html.parser")

    # 全機種URL取得
    kishu_link = soup2.select_one("a.btn1[href*='?kishu=all']")
    if kishu_link:
        kishu_href = kishu_link.get("href")
        if kishu_href and kishu_href.startswith("?"):
            kishu_url = latest_url.split("?")[0].rstrip("/") + "/" + kishu_href
        elif kishu_href and kishu_href.startswith("http"):
            kishu_url = kishu_href
        else:
            kishu_url = "https://min-repo.com" + kishu_href
        print(f"全機種URL: {kishu_url}")
        time.sleep(2)
        html3 = fetch_page(kishu_url)
        soup3 = BeautifulSoup(html3, "html.parser") if html3 else soup2
    else:
        soup3 = soup2

    # テーブル取得
    table_wrap2 = soup3.select_one("div.table_wrap")
    if not table_wrap2:
        print("データテーブルが見つかりません")
        return False

    table = table_wrap2.select_one("table")
    if not table:
        print("tableタグが見つかりません")
        return False

    rows = table.select("tr")
    if not rows:
        print("行データが見つかりません")
        return False

    # ── ヘッダー解析 ──
    header_row = rows[0]
    headers = [th.get_text(strip=True) for th in header_row.select("th, td")]
    print(f"ヘッダー: {headers}")

    # 列インデックスを特定
    col_map = {}
    for i, h in enumerate(headers):
        h_lower = h.lower().strip()
        if any(k in h_lower for k in ["機種", "name"]): col_map["機種"] = i
        elif any(k in h_lower for k in ["台番", "台no", "no"]): col_map["台番"] = i
        elif any(k in h_lower for k in ["差枚", "diff"]): col_map["差枚"] = i
        elif any(k in h_lower for k in ["g数", "回転", "game", "ゲーム"]): col_map["G数"] = i
        elif any(k in h_lower for k in ["出率", "rate", "bb", "rb"]): col_map["出率"] = i

    print(f"列マッピング: {col_map}")

    # ── データ行解析（parse_cellでマイナス判定）──
    data_rows = []
    debug_shown = 0
    for row in rows[1:]:
        cells = row.select("td")
        if not cells:
            continue

        # デバッグ: 230〜235行目あたり（マイナス台が出始める境界）を表示
        diff_idx = col_map.get("差枚", -1)
        if 225 <= debug_shown <= 235:
            all_texts = [c.get_text(strip=True) for c in cells]
            print(f"[DEBUG行{debug_shown+1}] 全テキスト={all_texts}")
            if diff_idx >= 0 and diff_idx < len(cells):
                print(f"  差枚HTML: {str(cells[diff_idx])[:400]}")
        debug_shown += 1

        row_data = {}
        for key, idx in col_map.items():
            if idx < len(cells):
                row_data[key] = parse_cell(cells[idx])
            else:
                row_data[key] = ""

        if row_data:
            data_rows.append(row_data)

    print(f"取得行数: {len(data_rows)}")

    # マイナスの台数確認
    if data_rows and "差枚" in col_map:
        minus_count = sum(1 for r in data_rows if isinstance(r.get("差枚"), float) and r["差枚"] < 0)
        plus_count = sum(1 for r in data_rows if isinstance(r.get("差枚"), float) and r["差枚"] > 0)
        print(f"差枚確認: プラス{plus_count}台 / マイナス{minus_count}台")

    if not data_rows:
        print("データが空です")
        return False

    # ── Google Sheetsに書き込み ──
    sheet = get_or_create_sheet(spreadsheet, date_str)
    sheet.clear()

    now_str = jst_now.strftime("%Y-%m-%d %H:%M")
    # ヘッダー
    out_headers = ["取得日時", "対象日付", "機種名", "台番", "差枚", "G数", "出率"]
    sheet.append_row(out_headers)

    batch = []
    for row_data in data_rows:
        batch.append([
            now_str,
            date_display,
            str(row_data.get("機種", "")),
            row_data.get("台番", ""),
            row_data.get("差枚", ""),
            row_data.get("G数", ""),
            row_data.get("出率", ""),
        ])

    for i in range(0, len(batch), 100):
        sheet.append_rows(batch[i:i+100])
        print(f"書き込み中... {min(i+100, len(batch))}/{len(batch)}")
        time.sleep(1)

    print(f"✅ {date_str} シートに {len(batch)} 行を保存しました")

    all_sheets = [ws.title for ws in spreadsheet.worksheets()]
    date_sheets = sorted([s for s in all_sheets if re.match(r"\d{4}-\d{2}-\d{2}", s)])
    print(f"蓄積済みシート: {date_sheets} ({len(date_sheets)}日分)")

    return True

if __name__ == "__main__":
    import sys
    # コマンドライン引数で日付指定可能
    # 例: python scraper_actions.py 2026-03-29
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target:
        print(f"指定日付モード: {target}")
    success = scrape_and_save(target_date=target)
    if success:
        print("🎉 正常完了")
        exit(0)
    else:
        print("⚠ 処理失敗")
        exit(1)
