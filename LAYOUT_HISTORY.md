# SlotDash 島図履歴

SlotDash の「島図」画面は Google Sheets の日付シートを選んで、その日の差枚・回転数・機種名を表示できます。

島配置そのものも日付ごとに切り替える場合は `data/layout_history.json` にバージョンを追加します。

```json
{
  "id": "cosmo-2026-09-20",
  "label": "2026-09-20 新台入替後",
  "effectiveFrom": "2026-09-20",
  "effectiveTo": "2026-10-05",
  "positionsFile": "data/layouts/cosmo-2026-09-20-positions.json",
  "backgroundFile": "data/layouts/cosmo-2026-09-20.png"
}
```

`positionsFile` は台番号をキーにした正規化座標です。

```json
{
  "positions": {
    "801": [0.9408, 0.9099],
    "802": [0.9408, 0.8894]
  }
}
```

- `effectiveFrom` / `effectiveTo` は YYYY-MM-DD。
- `effectiveTo` を省略するとその日以降ずっと有効です。
- 専用履歴がない日付は現行島図を使います。その場合、画面に「現行島図で表示」と警告が出ます。
- 過去日のデータだけを選べても、過去の配置スナップショットが保存されていない日を正確な過去島図として扱わないでください。

今後は新台入替などで配置が変わるタイミングだけ、新しい島図バージョンを追加すれば十分です。
