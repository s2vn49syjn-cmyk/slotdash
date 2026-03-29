"""
scraper_actions.py - GitHub Actions用スクレイパー
Selenium不要・requests+BeautifulSoupで動作
環境変数からGoogle Sheets認証情報を取得
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
SHEET_NAME = "スロデータ"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
}

# ─────────────────────────────────────────────
# Google Sheets接続
# ─────────────────────────────────────────────
def connect_sheets():
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
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    try:
        sheet = spreadsheet.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=1000, cols=20)

    return sheet

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
    yesterday = datetime.now() + timedelta(hours=9) - timedelta(days=1)  # JST
    date_str = yesterday.strftime("%Y/%m/%d")
    print(f"=== スクレイピング開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print(f"対象日付: {date_str}")

    # ① タグページ取得
    print(f"アクセス中: {TARGET_URL}")
    html = fetch_page(TARGET_URL)
    if not html:
        print("❌ タグページの取得失敗")
        return False

    soup = BeautifulSoup(html, "html.parser")

    # ② 最新レポートリンク取得
    table_wrap = soup.select_one("div.table_wrap")
    if not table_wrap:
        print("❌ table_wrapが見つかりません")
        return False

    latest_link = table_wrap.select_one("a")
    if not latest_link:
        print("❌ レポートリンクが見つかりません")
        return False

    latest_url = latest_link.get("href")
    print(f"最新レポートURL: {latest_url}")

    # ③ レポートページ取得
    time.sleep(2)
    html2 = fetch_page(latest_url)
    if not html2:
        print("❌ レポートページの取得失敗")
        return False

    soup2 = BeautifulSoup(html2, "html.parser")

    # ④ 全機種URLを取得
    kishu_link = soup2.select_one("a.btn1[href*='?kishu=all']")
    if kishu_link:
        kishu_url = kishu_link.get("href")
        print(f"全機種URL: {kishu_url}")
        time.sleep(2)
        html3 = fetch_page(kishu_url)
        if html3:
            soup3 = BeautifulSoup(html3, "html.parser")
        else:
            soup3 = soup2
    else:
        soup3 = soup2

    # ⑤ テーブルデータ取得
    table_wrap2 = soup3.select_one("div.table_wrap")
    if not table_wrap2:
        print("❌ データテーブルが見つかりません")
        return False

    table = table_wrap2.select_one("table")
    if not table:
        print("❌ tableタグが見つかりません")
        return False

    rows = table.select("tr")
    if not rows:
        print("❌ 行データが見つかりません")
        return False

    # ヘッダー取得
    header_row = rows[0]
    headers = [th.get_text(strip=True) for th in header_row.select("th, td")]
    print(f"ヘッダー: {headers}")

    # データ行取得
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
        print("❌ データが空です")
        return False

    # ⑥ Google Sheetsに書き込み
    print("Google Sheetsに接続中...")
    sheet = connect_sheets()
    sheet.clear()

    # ヘッダー書き込み
    full_headers = ["取得日時", "対象日付"] + headers
    sheet.append_row(full_headers)

    # データ書き込み（バッチ処理で高速化）
    now_str = (datetime.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")
    batch = []
    for row_data in data_rows:
        processed = [row_data[0] if row_data else ""]  # 台番or機種名はそのまま
        for i, val in enumerate(row_data):
            if i == 0:
                continue
            if i == 1:
                processed.append(val)  # 機種名はそのまま
            else:
                processed.append(parse_num(val))
        batch.append([now_str, date_str] + processed)

    # 100行ずつバッチ書き込み
    chunk_size = 100
    for i in range(0, len(batch), chunk_size):
        chunk = batch[i:i+chunk_size]
        sheet.append_rows(chunk)
        print(f"書き込み中... {min(i+chunk_size, len(batch))}/{len(batch)}")
        time.sleep(1)

    print(f"✅ 完了！{len(batch)}行をGoogle Sheetsに保存")
    return True

if __name__ == "__main__":
    success = scrape_and_save()
    if success:
        print("🎉 正常完了")
        exit(0)
    else:
        print("⚠ 処理失敗")
        exit(1)
