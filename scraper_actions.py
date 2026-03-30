"""
scraper_actions.py v2 - GitHub Actions用スクレイパー（日付別蓄積版）
毎日新しいシートにデータを蓄積する
既存の「スロデータ」シートは自動的に日付シートにコピーして保持
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

# ─────────────────────────────────────────────
# 設定
# ─────────────────────────────────────────────
TARGET_URL = "https://min-repo.com/tag/スーパーコスモプレミアム堺店/"
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
}

# ─────────────────────────────────────────────
# Google Sheets接続
# ─────────────────────────────────────────────
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
    """既存の「スロデータ」シートを日付シートに移行"""
    try:
        old_sheet = spreadsheet.worksheet("スロデータ")
        data = old_sheet.get_all_values()
        if not data:
            return
        date_str = "2026-03-29"
        if len(data) > 1 and data[1]:
            try:
                date_part = data[1][0].split(" ")[0] if data[1][0] else date_str
                if re.match(r"\d{4}-\d{2}-\d{2}", date_part):
                    date_str = date_part
            except:
                pass
        try:
            spreadsheet.worksheet(date_str)
            print(f"日付シート {date_str} は既に存在します。移行スキップ。")
        except gspread.WorksheetNotFound:
            new_sheet = spreadsheet.add_worksheet(title=date_str, rows=len(data)+10, cols=25)
            new_sheet.update(data)
            print(f"既存データを {date_str} シートに移行しました")
    except gspread.WorksheetNotFound:
        print("スロデータシートは見つかりませんでした（スキップ）")
    except Exception as e:
        print(f"移行エラー（続行）: {e}")

# ─────────────────────────────────────────────
# 数値パース
# ─────────────────────────────────────────────
def parse_num(text):
    if not text or text.strip() in ["-", "", "−", "ー"]:
        return ""
    cleaned = text.strip().replace(",", "").replace("＋", "+").replace("－", "-")
    m = re.search(r"[+-]?\d+", cleaned)
    return float(m.group()) if m else ""

# ─────────────────────────────────────────────
# ページ取得
# ─────────────────────────────────────────────
def fetch_page(url, retries=3):
    for i in range(retries):
        try:
            res = requests.get(url, headers=HEADERS, timeout=30)
            res.encoding = "utf-8"
            if res.status_code == 200:
                return res.text
            print(f"ステータス {res.status_code}: {url}")
        except Exception as e:
            print(f"リトライ {i+1}/{retries}: {e}")
            time.sleep(5)
    return None

# ─────────────────────────────────────────────
# メイン処理
# ─────────────────────────────────────────────
def scrape_and_save():
    jst_now = datetime.utcnow() + timedelta(hours=9)
    yesterday = jst_now - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    date_display = yesterday.strftime("%Y/%m/%d")

    print(f"=== スクレイピング開始: {jst_now.strftime('%Y-%m-%d %H:%M:%S')} JST ===")
    print(f"対象日付: {date_str}")

    print("Google Sheetsに接続中...")
    spreadsheet = connect_spreadsheet()
    migrate_old_data(spreadsheet)

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

    header_row = rows[0]
    headers = [th.get_text(strip=True) for th in header_row.select("th, td")]
    print(f"ヘッダー: {headers}")

    data_rows = []
    for row in rows[1:]:
        cells = row.select("td")
        if not cells:
            continue
        row_data = [c.get_text(strip=True) for c in cells]
        if row_data:
            data_rows.append(row_data)

    print(f"取得行数: {len(data_rows)}")
    if not data_rows:
        print("データが空です")
        return False

    sheet = get_or_create_sheet(spreadsheet, date_str)
    sheet.clear()

    now_str = jst_now.strftime("%Y-%m-%d %H:%M")
    full_headers = ["取得日時", "対象日付"] + headers
    sheet.append_row(full_headers)

    batch = []
    for row_data in data_rows:
        processed = []
        for i, val in enumerate(row_data):
            if i <= 1:
                processed.append(val)
            else:
                processed.append(parse_num(val))
        batch.append([now_str, date_display] + processed)

    for i in range(0, len(batch), 100):
        sheet.append_rows(batch[i:i+100])
        print(f"書き込み中... {min(i+100, len(batch))}/{len(batch)}")
        time.sleep(1)

    print(f"✅ {date_str} シートに {len(batch)} 行を保存しました")

    all_sheets = [ws.title for ws in spreadsheet.worksheets()]
    date_sheets = sorted([s for s in all_sheets if re.match(r"\d{4}-\d{2}-\d{2}", s)])
    print(f"蓄積済みシート: {date_sheets}")
    print(f"蓄積日数: {len(date_sheets)}日分")

    return True

if __name__ == "__main__":
    success = scrape_and_save()
    if success:
        print("🎉 正常完了")
        exit(0)
    else:
        print("⚠ 処理失敗")
        exit(1)
