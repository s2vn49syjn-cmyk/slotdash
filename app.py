      # ── 平均回転数ランキング ──
        st.markdown('<div class="sec-title">🔄 平均回転数ランキング（直近3日）</div>', unsafe_allow_html=True)

        # 除外機種の選択
        exclude_machines = st.multiselect(
            "除外する機種",
            options=sort_machines(df["機種名"].dropna().unique().tolist(), df),
            default=[],
            key="rot_exclude",
            placeholder="除外なし"
        )

        if history and len(sorted_dates) >= 1:
            rot_data = []
            for _, row in df.iterrows():
                if np.isnan(row["台番"]): continue
                if row["機種名"] in exclude_machines: continue
                num = int(row["台番"])
                mh = history.get(num, {})
                dates = sorted(mh.keys(), reverse=True)[:3]
@@ -1875,70 +1885,94 @@ def rec_card(row, tags, tag_color="#3b82f6"):
        else:
            df_t_sum = pd.DataFrame()

        rec_tabs = st.tabs(["❄️ 凹み×高回転", "⚠️ 大幅凹み", "📉 7日後凹み", "📉 6日後凹み", "🎰 ジャグラー"])
        # 機種ごとの設置台数を計算
        machine_counts = df["機種名"].value_counts().to_dict()

        def get_machines_by_count(target_count, exact=True):
            """設置台数がtarget_countの機種名リストを返す"""
            if exact:
                return [m for m, c in machine_counts.items() if c == target_count]
            else:
                return [m for m, c in machine_counts.items() if c >= target_count]

        def show_machine_group(count, exact=True, label=""):
            """指定台数構成の機種の直近3日差枚を悪い順に表示"""
            machines = get_machines_by_count(count, exact)
            if not machines:
                st.info(f"{label}の機種がありません")
                return
            # 対象台の直近3日差枚を計算
            rows = []
            for _, row in df_t.iterrows():
                if np.isnan(row["台番"]): continue
                if row["機種名"] not in machines: continue
                diffs = get_diffs(int(row["台番"]), 3)
                sum3 = sum(diffs) if diffs else np.nan
                rows.append((sum3, row))
            # 悪い順（差枚小さい順）
            rows = [r for r in rows if not (isinstance(r[0], float) and np.isnan(r[0]))]
            rows.sort(key=lambda x: x[0])
            if not rows:
                st.info("該当データなし")
                return
            st.markdown(f'<div style="font-size:0.65rem;color:#475569;margin-bottom:6px;">対象機種: {", ".join(shorten_name(m) for m in machines[:8])}{"..." if len(machines)>8 else ""}</div>', unsafe_allow_html=True)
            for sum3, row in rows[:12]:
                rec_card(row, [f"3日計 {int(sum3):+,}"], "#ef4444" if sum3 < 0 else "#22c55e")

        rec_tabs = st.tabs(["❄️ 3日連続凹×高回転", "🎯 3台構成", "🎯 4台構成", "🎯 8台構成", "🎯 16台↑", "🎰 ジャグ高回転"])

        with rec_tabs[0]:
            st.markdown('<div style="font-size:0.68rem;color:#94a3b8;margin-bottom:8px;">3日連続マイナス × 平均7000G以上</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:0.68rem;color:#94a3b8;margin-bottom:8px;">3日連続2000枚以下 × 平均6000G以上</div>', unsafe_allow_html=True)
            found = False
            cand = []
            for _, row in df_t.iterrows():
                if np.isnan(row["台番"]): continue
                diffs = get_diffs(int(row["台番"]), 3)
                rots = [r for r in get_rots(int(row["台番"]), 3) if not np.isnan(r)]
                if len(diffs) >= 3 and all(d < 0 for d in diffs) and rots and np.mean(rots) >= 7000:
                    rec_card(row, ["3日連続↓", f"avg {int(np.mean(rots)):,}G"], "#ef4444")
                    found = True
                # 3日連続で2000枚以下（マイナス〜微プラス含む）かつ平均6000G以上
                if len(diffs) >= 3 and all(d <= 2000 for d in diffs) and rots and np.mean(rots) >= 6000:
                    sum3 = sum(diffs)
                    cand.append((sum3, row, np.mean(rots)))
            cand.sort(key=lambda x: x[0])
            for sum3, row, avgr in cand[:12]:
                rec_card(row, [f"3日計{int(sum3):+,}", f"avg{int(avgr):,}G"], "#ef4444")
                found = True
            if not found: st.info("該当台なし")

        with rec_tabs[1]:
            st.markdown('<div style="font-size:0.68rem;color:#94a3b8;margin-bottom:8px;">前日-3000以下 × 7000G以上</div>', unsafe_allow_html=True)
            found = False
            for _, row in df_t.sort_values("前日差枚").iterrows():
                if np.isnan(row["台番"]): continue
                if not np.isnan(row["前日差枚"]) and row["前日差枚"] <= -3000 and not np.isnan(row["回転数"]) and row["回転数"] >= 7000:
                    rec_card(row, ["大幅凹み", f"{int(row['回転数']):,}G"], "#f97316")
                    found = True
            if not found: st.info("該当台なし")
            st.markdown('<div style="font-size:0.68rem;color:#94a3b8;margin-bottom:8px;">3台構成の機種・直近3日差枚が悪い順</div>', unsafe_allow_html=True)
            show_machine_group(3, exact=True, label="3台構成")

        with rec_tabs[2]:
            st.markdown('<div style="font-size:0.68rem;color:#94a3b8;margin-bottom:8px;">7日前+3000以上 → その後1000枚以下が続く台</div>', unsafe_allow_html=True)
            found = False
            for _, row in df_t.iterrows():
                if np.isnan(row["台番"]): continue
                diffs = get_diffs(int(row["台番"]), 7)
                if len(diffs) < 7: continue
                if diffs[-1] >= 3000 and all(d <= 1000 for d in diffs[:-1]):
                    rec_card(row, ["7日前大当り", "連日凹み"], "#a855f7")
                    found = True
            if not found: st.info("該当台なし")
            st.markdown('<div style="font-size:0.68rem;color:#94a3b8;margin-bottom:8px;">4台構成の機種・直近3日差枚が悪い順</div>', unsafe_allow_html=True)
            show_machine_group(4, exact=True, label="4台構成")

        with rec_tabs[3]:
            st.markdown('<div style="font-size:0.68rem;color:#94a3b8;margin-bottom:8px;">6日前+3000以上 → その後1000枚以下が続く台</div>', unsafe_allow_html=True)
            found = False
            for _, row in df_t.iterrows():
                if np.isnan(row["台番"]): continue
                diffs = get_diffs(int(row["台番"]), 6)
                if len(diffs) < 6: continue
                if diffs[-1] >= 3000 and all(d <= 1000 for d in diffs[:-1]):
                    rec_card(row, ["6日前大当り", "連日凹み"], "#8b5cf6")
                    found = True
            if not found: st.info("該当台なし")
            st.markdown('<div style="font-size:0.68rem;color:#94a3b8;margin-bottom:8px;">8台構成の機種・直近3日差枚が悪い順</div>', unsafe_allow_html=True)
            show_machine_group(8, exact=True, label="8台構成")

        with rec_tabs[4]:
            st.markdown('<div style="font-size:0.68rem;color:#94a3b8;margin-bottom:8px;">毎日プラス1000以下 × 回転数が増加傾向</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:0.68rem;color:#94a3b8;margin-bottom:8px;">16台以上の機種・直近3日差枚が悪い順</div>', unsafe_allow_html=True)
            show_machine_group(16, exact=False, label="16台以上")

        with rec_tabs[5]:
            st.markdown('<div style="font-size:0.68rem;color:#94a3b8;margin-bottom:8px;">ジャグラー・直近3日連続6000G以上（連日高回転）</div>', unsafe_allow_html=True)
            found = False
            df_jug = df_t[df_t["is_juggler"] == True]
            cand = []
            for _, row in df_jug.iterrows():
                if np.isnan(row["台番"]): continue
                diffs = get_diffs(int(row["台番"]), 3)
                rots = get_rots(int(row["台番"]), 3)
                valid_r = [r for r in rots if not np.isnan(r)]
                if len(diffs) < 2: continue
                if not all(0 < d <= 1000 for d in diffs): continue
                if len(valid_r) >= 2:
                    rots_asc = list(reversed(valid_r))
                    if all(rots_asc[i] < rots_asc[i+1] for i in range(len(rots_asc)-1)):
                        rec_card(row, ["小プラス継続", "回転↑"], "#06b6d4")
                        found = True
                # 直近3日すべて6000G以上
                if len(valid_r) >= 3 and all(r >= 6000 for r in valid_r):
                    diffs = get_diffs(int(row["台番"]), 3)
                    sum3 = sum(diffs) if diffs else 0
                    cand.append((np.mean(valid_r), sum3, row))
            cand.sort(key=lambda x: -x[0])  # 回転数多い順
            for avgr, sum3, row in cand[:12]:
                rec_card(row, [f"avg{int(avgr):,}G", f"3日計{int(sum3):+,}"], "#06b6d4")
                found = True
            if not found: st.info("該当台なし")

        # ── フィルタ ──
@@ -2035,31 +2069,10 @@ def chk_cont(num):
        else:
            st.markdown(f'<div style="font-size:0.72rem;color:#475569;margin:6px 0;">全台表示 {len(df_disp)}台</div>', unsafe_allow_html=True)

        # ── 全台テーブル ──
        def make_table(df_src):
            d = df_src.copy()
            d["台番"] = d["台番"].apply(lambda x: int(x) if not np.isnan(x) else "?")
            d["機種"] = d["機種名"].apply(shorten_name)
            d["前日"] = d["前日差枚"].apply(diff_sign)
            d["回転"] = d["回転数"].apply(lambda x: f"{int(x):,}" if not np.isnan(x) else "-")

            # 1日前・2日前・3日前G数
            if history and sorted_dates:
                d1 = sorted_dates[0] if len(sorted_dates) > 0 else None
                d2 = sorted_dates[1] if len(sorted_dates) > 1 else None
                d3 = sorted_dates[2] if len(sorted_dates) > 2 else None
                def gr(num, date):
                    if date is None or np.isnan(num): return "-"
                    mh = history.get(int(num), {})
                    r = mh.get(date, {}).get("rot", np.nan)
                    return f"{int(r):,}" if not np.isnan(r) else "-"
                d["1日前G"] = d["台番"].apply(lambda x: gr(x, d1) if x != "?" else "-")
                d["2日前G"] = d["台番"].apply(lambda x: gr(x, d2) if x != "?" else "-")
                d["3日前G"] = d["台番"].apply(lambda x: gr(x, d3) if x != "?" else "-")
                return d[["台番","機種","前日","回転","1日前G","2日前G","3日前G"]]
            return d[["台番","機種","前日","回転"]]

        st.dataframe(make_table(df_disp), hide_index=True, use_container_width=True, height=400)
        # フィルタ結果はカードで表示（全台テーブルは廃止）
        if active:
            for _, row in df_disp.head(30).iterrows():
                rec_card(row, [f"{shorten_name(row['機種名'])}"], "#3b82f6")


# ═══════════════════════════════════════════════════════
