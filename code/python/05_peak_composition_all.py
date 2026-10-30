import argparse
import os
from pathlib import Path

import pandas as pd

CLEAN_START = "20150301"
MIN_EVENTS = 20000
REGION_CODES = {"AFR", "ASA", "BLK", "EUR", "LAM", "MEA", "NAC", "SAS", "WST"}
FEATURED = ["AFG", "UKR", "PRK", "TWN", "IRN", "VEN", "SAU"]


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=str(root / "data" / "processed"))
    parser.add_argument("--output-dir", default=str(root / "data" / "analysis"))
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    visibility = pd.read_csv(os.path.join(args.input_dir, "visibility_daily.csv"), dtype={"date": str})
    visibility = visibility[(visibility["date"] >= CLEAN_START) & (~visibility["country"].isin(REGION_CODES))].copy()
    visibility["month"] = visibility["date"].str[:6]
    monthly = visibility.groupby(["month", "country"])["n_events"].sum().reset_index()
    totals = monthly.groupby("month")["n_events"].sum().rename("tot")
    monthly = monthly.merge(totals, on="month")
    monthly["share"] = monthly["n_events"] / monthly["tot"] * 100
    usa = visibility[visibility["country"] == "USA"].groupby("month")["n_events"].sum()
    usa_share = usa / totals * 100
    months = sorted(totals.index)
    rows = []
    for country, frame in monthly.groupby("country"):
        if frame["n_events"].sum() < MIN_EVENTS:
            continue
        top = frame.sort_values("share", ascending=False).iloc[0]
        peak_month = top["month"]
        index = months.index(peak_month)
        baseline_months = [months[j] for j in range(max(0, index - 6), min(len(months), index + 7)) if j != index]
        baseline = usa_share[baseline_months].mean()
        rows.append({"country": country, "peak_month": peak_month, "peak_share": round(top["share"], 2),
                     "usa_share_peak": round(usa_share[peak_month], 2),
                     "usa_share_base": round(baseline, 2),
                     "deviation": round(usa_share[peak_month] - baseline, 2)})
    result = pd.DataFrame(rows).sort_values("deviation", ascending=False).reset_index(drop=True)
    result.to_csv(os.path.join(args.output_dir, "e4_peak_composition_all.csv"), index=False, encoding="utf-8-sig")
    deviation = result["deviation"]
    lines = ["=== E4 峰值月构成效应：全样本 ===",
             f"实体数 {len(result)}（事件量 ≥ {MIN_EVENTS}；干净窗口 {CLEAN_START} 起）",
             f"偏离中位数 {deviation.median():+.2f}｜均值 {deviation.mean():+.2f}｜标准差 {deviation.std():.2f}"]
    for tolerance in (1.0, 1.7, 2.0, 3.0):
        count = int((deviation.abs() <= tolerance).sum())
        lines.append(f"|偏离| ≤ {tolerance:.1f} 个百分点：{count} 个实体（{count / len(result) * 100:.1f}%）")
    lines.append(f"偏离 > +1.7 个百分点：{int((deviation > 1.7).sum())} 个实体")
    lines.append("")
    lines.append(result.head(10).to_string(index=False))
    lines.append("")
    lines.append(result.tail(10).to_string(index=False))
    lines.append("")
    for country in FEATURED:
        selected = result[result["country"] == country]
        if selected.empty:
            continue
        row = selected.iloc[0]
        percentile = (deviation < row["deviation"]).mean() * 100
        lines.append(f"{country} 峰值月 {row['peak_month']}：偏离 {row['deviation']:+.2f} 个百分点；"
                     f"百分位 {percentile:.0f}")
    text = "\n".join(lines)
    with open(os.path.join(args.output_dir, "e4_peak_composition_all.txt"), "w", encoding="utf-8") as stream:
        stream.write(text)
    print(text)


if __name__ == "__main__":
    main()
