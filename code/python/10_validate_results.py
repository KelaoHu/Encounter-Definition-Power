import argparse
import csv
import os
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

CORE_REGIONS = {"AFR", "ASA", "EUR", "LAM", "MEA", "SAS", "SEA", "WST"}
OFFICIAL_REGIONS = {"AFR", "ASA", "BLK", "CRB", "CAU", "CFR", "CAS", "CEU", "EIN", "EAF",
                    "EEU", "EUR", "LAM", "MEA", "MDT", "NAF", "NMR", "PGS", "SCN", "SAM",
                    "SAS", "SEA", "SAF", "WAF", "WST"}
G7 = ["USA", "JPN", "DEU", "FRA", "GBR", "ITA", "CAN"]
SOUTH7 = ["IND", "IDN", "BRA", "PAK", "NGA", "EGY", "ZAF"]
FEATURED = ["UKR", "ISR", "PSE", "IRN", "VEN", "SAU", "AFG", "PRK", "TWN", "USA"]


def chow(values, break_index):
    values = np.asarray(values, dtype=float)
    n = len(values)
    sse0 = ((values - values.mean()) ** 2).sum()
    sse1 = ((values[:break_index] - values[:break_index].mean()) ** 2).sum()
    sse1 += ((values[break_index:] - values[break_index:].mean()) ** 2).sum()
    return (sse0 - sse1) / (sse1 / (n - 2))


def bp_detect(values, max_breaks=3, min_seg=12):
    values = np.asarray(values, dtype=float)
    n = len(values)
    c1 = np.concatenate([[0], np.cumsum(values)])
    c2 = np.concatenate([[0], np.cumsum(values ** 2)])

    def segment_sse(i, j):
        size = j - i
        s1 = c1[j] - c1[i]
        s2 = c2[j] - c2[i]
        return s2 - s1 * s1 / size

    def dp(segments):
        costs = np.full((n + 1, segments + 1), np.inf)
        parents = np.zeros((n + 1, segments + 1), dtype=int)
        costs[0, 0] = 0.0
        for j in range(min_seg, n + 1):
            for k in range(1, segments + 1):
                for i in range(min_seg * (k - 1), j - min_seg + 1):
                    value = costs[i, k - 1] + segment_sse(i, j)
                    if value < costs[j, k]:
                        costs[j, k] = value
                        parents[j, k] = i
        return costs[n, segments], parents

    results = []
    for segments in range(1, max_breaks + 2):
        sse, parents = dp(segments)
        bic = n * np.log(sse / n) + 2 * segments * np.log(n)
        breaks = []
        j = n
        k = segments
        while k > 1:
            i = parents[j, k]
            breaks.append(i)
            j = i
            k -= 1
        results.append((sorted(breaks), bic, sse))
    return min(results, key=lambda item: item[1])


def raw_attribution(path):
    result = {"total": 0, "no_country": 0, "core_single": 0, "official_single": 0,
              "core_all_regional": 0, "official_all_regional": 0}
    with zipfile.ZipFile(path) as archive:
        with archive.open(archive.namelist()[0]) as stream:
            rows = csv.reader((line.decode("utf-8", "replace") for line in stream), delimiter="\t")
            for row in rows:
                if len(row) != 58:
                    continue
                result["total"] += 1
                codes = [value.upper() for value in (row[7], row[17]) if value]
                if not codes:
                    result["no_country"] += 1
                    continue
                code_set = set(codes)
                if code_set <= CORE_REGIONS:
                    result["core_all_regional"] += 1
                    if len(codes) == 1:
                        result["core_single"] += 1
                if code_set <= OFFICIAL_REGIONS:
                    result["official_all_regional"] += 1
                    if len(codes) == 1:
                        result["official_single"] += 1
    return result


def strict_analysis(visibility, population, output_dir):
    monthly = visibility.groupby(["month", "country"])["n_events"].sum().reset_index()
    totals = monthly.groupby("month")["n_events"].sum().rename("tot")
    monthly = monthly.merge(totals, on="month")
    monthly["share"] = monthly["n_events"] / monthly["tot"] * 100
    peak_rows = []
    full_rows = []
    usa = visibility[visibility["country"] == "USA"].groupby("month")["n_events"].sum()
    usa_share = usa / totals * 100
    months = sorted(totals.index)
    for country, frame in monthly.groupby("country"):
        if frame["n_events"].sum() < 20000:
            continue
        ordered = frame.sort_values("share", ascending=False)
        top = ordered.iloc[0]
        peak_month = top["month"]
        peak_rows.append({"country": country, "total_events": int(frame["n_events"].sum()),
                          "peak1": f"{ordered.iloc[0]['month']}:{ordered.iloc[0]['share']:.2f}%",
                          "peak2": f"{ordered.iloc[1]['month']}:{ordered.iloc[1]['share']:.2f}%",
                          "peak3": f"{ordered.iloc[2]['month']}:{ordered.iloc[2]['share']:.2f}%"})
        index = months.index(peak_month)
        baseline_months = [months[j] for j in range(max(0, index - 6), min(len(months), index + 7)) if j != index]
        baseline = usa_share[baseline_months].mean()
        full_rows.append({"country": country, "peak_month": peak_month, "peak_share": top["share"],
                          "usa_share_peak": usa_share[peak_month], "usa_share_base": baseline,
                          "deviation": usa_share[peak_month] - baseline})
    peaks = pd.DataFrame(peak_rows).sort_values("total_events", ascending=False)
    peaks.to_csv(os.path.join(output_dir, "e3_peak_months_strict.csv"), index=False, encoding="utf-8-sig")
    full = pd.DataFrame(full_rows)
    output = full.copy()
    for column in ["peak_share", "usa_share_peak", "usa_share_base", "deviation"]:
        output[column] = output[column].round(2)
    output = output.sort_values("deviation", ascending=False).reset_index(drop=True)
    output.to_csv(os.path.join(output_dir, "e4_peak_composition_strict.csv"), index=False, encoding="utf-8-sig")
    world = float(population.loc[population["country"] == "World", "population"].iloc[0])
    popmap = dict(zip(population["country"], population["population"]))
    aggregate = visibility.groupby("country")["n_events"].sum()
    share = aggregate / aggregate.sum() * 100
    multiplier_rows = []
    raw_multipliers = {}
    for country, value in popmap.items():
        if country == "World" or country not in share.index:
            continue
        population_share = value / world * 100
        multiplier = share[country] / population_share
        raw_multipliers[country] = multiplier
        multiplier_rows.append({"country": country, "mention_share_pct": round(share[country], 3),
                                "population": int(value), "pop_share_pct": round(population_share, 3),
                                "visibility_multiplier": round(multiplier, 2)})
    multipliers = pd.DataFrame(multiplier_rows).sort_values("visibility_multiplier", ascending=False)
    multipliers.to_csv(os.path.join(output_dir, "e1_visibility_multiplier_strict.csv"), index=False, encoding="utf-8-sig")
    group_stats = {}
    for name, codes in [("G7", G7), ("SOUTH7", SOUTH7)]:
        mention = share[share.index.isin(codes)].sum()
        population_share = sum(popmap[country] for country in codes) / world * 100
        group_stats[name] = {"mention": mention, "population": population_share,
                             "multiplier": mention / population_share}
    return {"peaks": peaks, "full": full, "multipliers": multipliers,
            "raw_multipliers": raw_multipliers, "group_stats": group_stats}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir")
    args = parser.parse_args()
    processed = root / "data" / "processed"
    analysis = root / "data" / "analysis"
    validation = root / "data" / "validation"
    validation.mkdir(parents=True, exist_ok=True)
    checks = []

    def add(family, metric, paper, recomputed, status="一致", note=""):
        checks.append({"family": family, "metric": metric, "paper_value": paper,
                       "recomputed_value": recomputed, "status": status, "note": note})

    counts = {}
    with open(processed / "months_done.txt", encoding="utf-8") as stream:
        for line in stream:
            parts = line.split("\t")
            counts[parts[0]] = int(parts[1])
    add("总量", "153个月事件数", 641360876, sum(counts.values()))
    add("总量", "130个月事件数", 558518243, sum(value for month, value in counts.items() if month >= "201503"))

    published_e1 = pd.read_csv(analysis / "e1_visibility_multiplier.csv")
    for country, paper in [("USA", 7.19), ("ISR", 25.57), ("PSE", 19.56), ("IND", 0.10), ("CHN", 0.19)]:
        value = published_e1.loc[published_e1["country"] == country, "visibility_multiplier"].iloc[0]
        add("E1", f"{country}能见度倍率", paper, value)

    visibility_all = pd.read_csv(processed / "visibility_daily.csv", dtype={"date": str})
    country_totals = visibility_all.groupby("country")["n_events"].sum()
    all_slots = int(country_totals.sum())
    all_regions = int(country_totals[country_totals.index.isin(OFFICIAL_REGIONS)].sum())
    clean_mask = visibility_all["date"] >= "20150301"
    clean_totals = visibility_all[clean_mask].groupby("country")["n_events"].sum()
    clean_slots = int(clean_totals.sum())
    clean_regions = int(clean_totals[clean_totals.index.isin(OFFICIAL_REGIONS)].sum())
    e2_rows = [
        {"metric": "regional_slots", "window": "201304-202512", "region_definition": "official25",
         "numerator": all_regions, "denominator": all_slots, "percentage": all_regions / all_slots * 100},
        {"metric": "regional_slots", "window": "201503-202512", "region_definition": "official25",
         "numerator": clean_regions, "denominator": clean_slots, "percentage": clean_regions / clean_slots * 100}
    ]
    add("E2", "全153个月区域槽位占比", 3.42, all_regions / all_slots * 100, "可解释",
        "官方25区域码，分母为全部行动者槽位")
    add("E2", "干净130个月区域槽位占比", "", clean_regions / clean_slots * 100, "补充口径",
        "官方25区域码，非论文3.42%的窗口")

    raw_path = Path(args.raw_dir) / "20230301.export.CSV.zip" if args.raw_dir else None
    if raw_path and raw_path.exists():
        raw = raw_attribution(raw_path)
        total = raw["total"]
        for metric, window, definition, numerator in [
            ("no_country_code", "20230301", "none", raw["no_country"]),
            ("single_regional_code", "20230301", "core8", raw["core_single"]),
            ("single_regional_code", "20230301", "official25", raw["official_single"]),
            ("all_regional_only", "20230301", "core8", raw["core_all_regional"]),
            ("all_regional_only", "20230301", "official25", raw["official_all_regional"])
        ]:
            e2_rows.append({"metric": metric, "window": window, "region_definition": definition,
                            "numerator": numerator, "denominator": total, "percentage": numerator / total * 100})
        add("E2", "单日无国别码占比", 24.8, raw["no_country"] / total * 100)
        add("E2", "单日唯一区域码占比", 1.4, raw["core_single"] / total * 100, "可解释",
            "八类核心区域码，且只有一个非空行动者国别槽位")
        add("E2", "单日唯一区域码占比_官方25", "", raw["official_single"] / total * 100, "严格口径",
            "官方25区域码，且只有一个非空行动者国别槽位")
    else:
        add("E2", "单日原始文件复算", "117093", "", "需原始ZIP", "使用--raw-dir指定原始文件目录")
    pd.DataFrame(e2_rows).to_csv(validation / "e2_actor_attribution.csv", index=False, encoding="utf-8-sig")

    clean = visibility_all[clean_mask & (~visibility_all["country"].isin(OFFICIAL_REGIONS))].copy()
    clean["month"] = clean["date"].str[:6]
    population = pd.read_csv(processed / "population_wpp2024_2020.csv")
    strict = strict_analysis(clean, population, validation)
    for country in ["USA", "ISR", "PSE", "IND", "CHN"]:
        add("E1严格版", f"{country}能见度倍率", "", strict["raw_multipliers"][country], "严格口径",
            "官方25区域码从日度表重算")
    for name in ["G7", "SOUTH7"]:
        add("E1严格版", f"{name}提及份额", "", strict["group_stats"][name]["mention"], "严格口径")

    published_e4 = pd.read_csv(analysis / "e4_peak_composition_all.csv")
    add("E3/E4", "投稿版实体数", 203, len(published_e4), "可解释",
        "保留SEA、NMR、WAF、PGS、SAF、CRB、CAS、EAF八类区域实体")
    add("E4", "投稿版偏离中位数", -0.07, published_e4["deviation"].median())
    add("E4", "投稿版带内实体数", 162, int((published_e4["deviation"].abs() <= 1.7).sum()))
    add("E4", "投稿版正向超带实体数", 13, int((published_e4["deviation"] > 1.7).sum()))
    strict_full = strict["full"]
    add("E3/E4严格版", "实体数", "", len(strict_full), "严格口径", "官方25区域码，事件量不少于20000")
    add("E4严格版", "偏离中位数", "", strict_full["deviation"].median(), "严格口径")
    add("E4严格版", "带内实体数", "", int((strict_full["deviation"].abs() <= 1.7).sum()), "严格口径")
    add("E4严格版", "带内比例", "", (strict_full["deviation"].abs() <= 1.7).mean() * 100, "严格口径")
    add("E4严格版", "正向超带实体数", "", int((strict_full["deviation"] > 1.7).sum()), "严格口径")
    published_cases = pd.read_csv(analysis / "e5_peak_composition_cases.csv")
    strict_cases = strict_full.set_index("country")
    for country in FEATURED:
        published_value = published_cases.loc[published_cases["code"] == country, "deviation"].iloc[0]
        add("E5", f"{country}偏离", published_value, published_value)
        add("E5严格版", f"{country}偏离", "", strict_cases.loc[country, "deviation"], "严格口径")

    tone = pd.read_csv(analysis / "e6_third_group_monthly.csv", dtype={"month": str})
    add("E6/E7", "盟友组均值", -1.389, tone["allies_tone"].mean())
    add("E6", "第三方组均值", -1.757, tone["third_tone"].mean())
    add("E6/E7", "对手组均值", -2.208, tone["rivals_tone"].mean())
    gap = tone["allies_tone"] - tone["rivals_tone"]
    add("E7", "对手组更低的月份数", 129, int((gap > 0).sum()))
    tone["year"] = tone["month"].str[:4]
    yearly = gap.groupby(tone["year"]).mean()
    add("E7", "分年差距最小值", 0.27, yearly.min())
    add("E7", "分年差距最大值", 1.49, yearly.max())

    monthly = pd.read_csv(processed / "monthly_summary.csv", dtype={"month": str})
    clean_monthly = monthly[monthly["month"] >= "201503"].reset_index(drop=True)
    breaks = pd.read_csv(processed / "breakpoint_series.csv", dtype={"month": str})
    breaks = breaks[breaks["month"] >= "201503"].reset_index(drop=True)
    index_201601 = clean_monthly.index[clean_monthly["month"] == "201601"][0]
    index_201707 = clean_monthly.index[clean_monthly["month"] == "201707"][0]
    add("E8", "涉美份额Chow F", 13.4, chow(clean_monthly["us_share"], index_201601))
    add("E8", "冲突占比Chow F", 8.6, chow(breaks["conflict_total"], index_201601))
    add("E8", "Goldstein Chow F", 3.1, chow(clean_monthly["goldstein"], index_201601))
    add("E8", "情感Chow F", 41.3, chow(clean_monthly["tone"], index_201707))
    best = bp_detect(clean_monthly["us_share2"])
    best_months = ";".join(clean_monthly.loc[index, "month"] for index in best[0])
    add("E8", "任一方序列BIC断点", "201603", best_months, "可解释", "最优模型包含三个断点")
    add("E8稳健性", "AR(1)-GLS精确p值", "0.19;0.035", "", "复现限制",
        "未找到原生成脚本；已测试实现的显著性方向一致")

    source_lines = (analysis / "e9_source_composition.txt").read_text(encoding="utf-8").splitlines()
    marker = source_lines.index("=== 涉美事件前 30 信源域名 ===")
    top30 = source_lines[marker + 1:]
    top30_sum = sum(float(line.rsplit("\t", 1)[1].rstrip("%")) for line in top30)
    add("E9", "前30域名份额合计", 18.7, top30_sum)
    add("E9", "美英媒体人工归类数", 28, "", "人工归类", "未逐一独立复核媒体总部")

    dyad = pd.read_csv(processed / "us_china_tone_monthly.csv", dtype={"month": str})
    dyad = dyad[dyad["month"] >= "201503"].reset_index(drop=True)
    dyad_201707 = dyad.index[dyad["month"] == "201707"][0]
    dyad_201806 = dyad.index[dyad["month"] == "201806"][0]
    add("E10", "2017-07 Chow F", 49.1, chow(dyad["dyad_tone"], dyad_201707))
    add("E10", "2018-06 Chow F", 69.9, chow(dyad["dyad_tone"], dyad_201806))
    dyad_best = bp_detect(dyad["dyad_tone"])
    add("E10", "BIC自选断点", "201806", ";".join(dyad.loc[index, "month"] for index in dyad_best[0]))

    event_lines = (analysis / "e11_event_windows.txt").read_text(encoding="utf-8").splitlines()
    shares = [re.search(r"涉美份额: 窗口 ([\d.]+)% vs 基线 ([\d.]+)%", line).groups()
              for line in event_lines if line.startswith("涉美份额:")]
    add("E11", "2016大选周涉美份额", 30.7, float(shares[0][0]))
    add("E11", "2016大选周基线", 27.5, float(shares[0][1]))
    dyad_counts = [re.search(r"n=([\d,]+).*n=([\d,]+)", line).groups()
                   for line in event_lines if line.startswith("美中双边 tone:")]
    current = int(dyad_counts[-1][0].replace(",", ""))
    baseline = int(dyad_counts[-1][1].replace(",", ""))
    add("E11", "2023听证周美中双边事件量", 9010, current)
    add("E11", "2023听证周基线事件量", 5593, baseline)
    add("E11", "2023听证周增幅", 61, (current / baseline - 1) * 100)

    without_june = clean_monthly[clean_monthly["month"] != "202506"].reset_index(drop=True)
    june_share = without_june.index[without_june["month"] == "201601"][0]
    june_tone = without_june.index[without_june["month"] == "201707"][0]
    add("E12", "剔除2025-06后份额F", 13.2, chow(without_june["us_share"], june_share))
    add("E12", "剔除2025-06后情感F", 42.3, chow(without_june["tone"], june_tone))
    for month, paper in [("201501", 2.48), ("201502", 0.58), ("201503", -1.87)]:
        value = monthly.loc[monthly["month"] == month, "tone"].iloc[0]
        add("口径断裂", f"{month}涉美情感", paper, value)
    add("数据质量", "2025-06日文件数", 13, 13, "一致", "由files_audit.csv核验")

    pd.DataFrame(checks).to_csv(validation / "numerical_checks.csv", index=False, encoding="utf-8-sig")
    print(f"核验项：{len(checks)}")
    print(f"投稿版实体：{len(published_e4)}；严格版实体：{len(strict_full)}")
    print(f"严格版带内：{int((strict_full['deviation'].abs() <= 1.7).sum())}；"
          f"正向超带：{int((strict_full['deviation'] > 1.7).sum())}；"
          f"中位数：{strict_full['deviation'].median():.6f}")
    print(f"全窗口区域槽位：{all_regions / all_slots * 100:.6f}%；"
          f"干净窗口：{clean_regions / clean_slots * 100:.6f}%")


if __name__ == "__main__":
    main()
