import argparse
import os
from pathlib import Path

import pandas as pd

CLEAN_START = "20150301"
REGION_CODES = {"AFR", "ASA", "BLK", "EUR", "LAM", "MEA", "NAC", "SAS", "WST"}
CASES = [
    ("UKR", "乌克兰", "202203", "2022-03 俄乌冲突爆发月：同月俄、波、摩、拉脱维亚均为 −6.29"),
    ("ISR", "以色列", "202310", "2023-10 新一轮巴以冲突爆发月：同月巴勒斯坦、埃及、约旦、阿鲁巴均为 −4.28"),
    ("PSE", "巴勒斯坦", "202310", "2023-10 同月：与以色列同月"),
    ("IRN", "伊朗", "202001", "苏莱曼尼事件月"),
    ("VEN", "委内瑞拉", "201902", "基线附近"),
    ("SAU", "沙特阿拉伯", "201810", "基线附近"),
    ("AFG", "阿富汗", "202108", "基线附近：美军撤离月"),
    ("PRK", "朝鲜", "201806", "基线附近：金特会月"),
    ("TWN", "中国台湾地区", "202208", "基线附近"),
    ("USA", "美国（自身）", "202101", "参照个案：其峰值即自身议程高峰")
]


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
    totals = visibility.groupby("month")["n_events"].sum()
    usa = visibility[visibility["country"] == "USA"].groupby("month")["n_events"].sum()
    usa_share = usa / totals * 100
    months = sorted(totals.index)
    rows = []
    lines = [f"全窗口美国提及份额均值 {usa_share.mean():.2f}%"]
    for code, name, peak_month, note in CASES:
        index = months.index(peak_month)
        baseline_months = months[max(0, index - 6):index] + months[index + 1:index + 7]
        baseline = usa_share[baseline_months].mean()
        peak = usa_share[peak_month]
        country_events = visibility[(visibility["country"] == code) &
                                    (visibility["month"] == peak_month)]["n_events"].sum()
        country_share = country_events / totals[peak_month] * 100
        deviation = peak - baseline
        rows.append({"code": code, "name": name, "peak_month": peak_month,
                     "usa_share_peak": round(peak, 2), "usa_share_base": round(baseline, 2),
                     "deviation": round(deviation, 2), "note": note})
        lines.append(f"{code} 峰值月 {peak_month}: 该国份额 {country_share:.1f}%；"
                     f"当月美国份额 {peak:.1f}%（基线 {baseline:.1f}%，偏离 {deviation:+.1f} 个百分点）")
    frame = pd.DataFrame(rows)
    frame.to_csv(os.path.join(args.output_dir, "e5_peak_composition_cases.csv"), index=False, encoding="utf-8-sig")
    text = "\n".join(lines)
    with open(os.path.join(args.output_dir, "e5_peak_composition_cases.txt"), "w", encoding="utf-8") as stream:
        stream.write(text)
    print(text)


if __name__ == "__main__":
    main()
