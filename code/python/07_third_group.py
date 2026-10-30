import argparse
import os
from math import erfc, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

ALLIES = ["GBR", "CAN", "AUS", "NZL", "FRA", "DEU", "ITA"]
RIVALS = ["CHN", "RUS", "IRN", "PRK"]
THIRD = ["IDN", "BRA", "ZAF", "NGA"]
CLEAN_START = "20150301"
CANDIDATE_BREAKS = ["201806", "202202"]


def chow(values, break_index):
    values = np.asarray(values, dtype=float)
    n = len(values)
    sse0 = ((values - values.mean()) ** 2).sum()
    sse1 = ((values[:break_index] - values[:break_index].mean()) ** 2).sum()
    sse1 += ((values[break_index:] - values[break_index:].mean()) ** 2).sum()
    return (sse0 - sse1) / (sse1 / (n - 2))


def p_approx(statistic):
    return erfc(sqrt(statistic / 2))


def bh(pvalues):
    order = np.argsort(pvalues)
    m = len(pvalues)
    adjusted = [None] * m
    running = 1.0
    for rank, index in enumerate(reversed(order), start=1):
        k = m - rank + 1
        running = min(running, pvalues[index] * m / k)
        adjusted[index] = running
    return adjusted


def group_series(visibility, group):
    frame = visibility[visibility["country"].isin(group)]
    return frame.groupby("month").apply(
        lambda values: np.average(values["tone_mean"], weights=values["n_events"])
        if values["n_events"].sum() > 0 else np.nan,
        include_groups=False)


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=str(root / "data" / "processed"))
    parser.add_argument("--output-dir", default=str(root / "data" / "analysis"))
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    visibility = pd.read_csv(os.path.join(args.input_dir, "visibility_daily.csv"), dtype={"date": str})
    visibility = visibility[visibility["date"] >= CLEAN_START].copy()
    visibility["month"] = visibility["date"].str[:6]
    visibility = visibility.dropna(subset=["tone_mean"])
    allied = group_series(visibility, ALLIES)
    rival = group_series(visibility, RIVALS)
    third = group_series(visibility, THIRD)
    common = allied.index.intersection(rival.index).intersection(third.index)
    allied = allied[common]
    rival = rival[common]
    third = third[common]
    lines = [f"窗口：{common[0]} 至 {common[-1]}，共 {len(common)} 个月",
             f"盟友组全期情感均值 {allied.mean():.3f}；第三方组 {third.mean():.3f}；对手组 {rival.mean():.3f}",
             f"第三方组均值与盟友组的距离 {third.mean() - allied.mean():.3f}；与对手组的距离 {third.mean() - rival.mean():.3f}",
             f"对手 < 第三方 < 盟友排序成立的月份占比：{((rival < third) & (third < allied)).mean() * 100:.0f}%"]
    all_p = []
    labels = []
    for candidate in CANDIDATE_BREAKS:
        if candidate not in common:
            continue
        index = list(common).index(candidate)
        for name, series in [("第三方组自身", third), ("盟友组自身", allied), ("对手组自身", rival)]:
            statistic = chow(series.values, index)
            pvalue = p_approx(statistic)
            all_p.append(pvalue)
            labels.append(f"{name}断点@{candidate}")
            lines.append(f"{name} {candidate}: Chow F={statistic:.2f}（近似 p={pvalue:.4f}）；"
                         f"断点前 {series.values[:index].mean():.3f} → 断点后 {series.values[index:].mean():.3f}")
    inside = []
    for country in THIRD:
        mean_value = group_series(visibility, [country])[common].mean()
        inside.append(mean_value)
        lines.append(f"第三方组内 {country} 全期均值 {mean_value:.3f}")
    lines.append(f"第三方组内四国均值极差 {max(inside) - min(inside):.3f}；"
                 f"盟友与对手组间差 {allied.mean() - rival.mean():.3f}")
    adjusted = bh(all_p)
    lines.append("=== BH 校正后 ===")
    for label, pvalue, qvalue in zip(labels, all_p, adjusted):
        lines.append(f"{label}: p={pvalue:.4f} → BH q={qvalue:.4f}")
    pd.DataFrame({"month": common, "allies_tone": allied.values, "third_tone": third.values,
                  "rivals_tone": rival.values, "diff_rival_allies": (rival - allied).values}).to_csv(
        os.path.join(args.output_dir, "e6_third_group_monthly.csv"), index=False, encoding="utf-8-sig")
    text = "\n".join(lines)
    with open(os.path.join(args.output_dir, "e6_third_group.txt"), "w", encoding="utf-8") as stream:
        stream.write(text)
    print(text)


if __name__ == "__main__":
    main()
