import argparse
import os
from math import erfc, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

ALLIES_A = ["GBR", "CAN", "AUS", "NZL", "FRA", "DEU", "ITA"]
ALLIES_B = ALLIES_A + ["JPN", "KOR", "NLD", "ESP", "POL", "BEL"]
RIVALS_A = ["CHN", "RUS", "IRN", "PRK"]
RIVALS_B = RIVALS_A + ["CUB", "VEN", "SYR"]
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
    lines = []
    all_p = []
    labels = []
    for allies_name, allies in [("A 五眼+北约核心", ALLIES_A), ("B 加条约盟友", ALLIES_B)]:
        for rivals_name, rivals in [("A 核心四国", RIVALS_A), ("B 加扩展", RIVALS_B)]:
            def group_series(group):
                frame = visibility[visibility["country"].isin(group)]
                return frame.groupby("month").apply(
                    lambda values: np.average(values["tone_mean"], weights=values["n_events"])
                    if values["n_events"].sum() > 0 else np.nan,
                    include_groups=False)

            allied = group_series(allies)
            rival = group_series(rivals)
            common = allied.index.intersection(rival.index)
            allied = allied[common]
            rival = rival[common]
            difference = rival - allied
            lines.append(f"=== 盟友组{allies_name} vs 对手组{rivals_name} ===")
            lines.append(f"盟友组全期情感均值 {allied.mean():.3f}；对手组 {rival.mean():.3f}；组差 {difference.mean():.3f}")
            lines.append(f"对手组情感低于盟友组的月份占比：{(difference < 0).mean() * 100:.0f}%（n={len(difference)} 个月）")
            for candidate in CANDIDATE_BREAKS:
                if candidate not in common:
                    continue
                index = list(common).index(candidate)
                statistic = chow(difference.values, index)
                pvalue = p_approx(statistic)
                all_p.append(pvalue)
                labels.append(f"组差断点@{candidate} [{allies_name}/{rivals_name}]")
                lines.append(f"组差序列断点 {candidate}: Chow F={statistic:.2f}（近似 p={pvalue:.4f}）；"
                             f"断点前组差 {difference.values[:index].mean():.3f} → 断点后组差 {difference.values[index:].mean():.3f}")
            for segment_name, segment in [("2015-03~2018-05", difference["201503":"201805"]),
                                          ("2018-06~2022-01", difference["201806":"202201"]),
                                          ("2022-02~2025-12", difference["202202":"202512"])]:
                if len(segment):
                    lines.append(f"{segment_name}: 组差均值 {segment.mean():.3f}")
            lines.append("")
            if allies_name.startswith("A") and rivals_name.startswith("A"):
                pd.DataFrame({"month": common, "allies_tone": allied.values,
                              "rivals_tone": rival.values, "diff": difference.values}).to_csv(
                    os.path.join(args.output_dir, "e7_group_tone_monthly.csv"), index=False, encoding="utf-8-sig")
    adjusted = bh(all_p)
    lines.append("=== BH 校正后 ===")
    for label, pvalue, qvalue in zip(labels, all_p, adjusted):
        lines.append(f"{label}: p={pvalue:.4f} → BH q={qvalue:.4f}")
    text = "\n".join(lines)
    with open(os.path.join(args.output_dir, "e7_group_tone.txt"), "w", encoding="utf-8") as stream:
        stream.write(text)
    print(text)


if __name__ == "__main__":
    main()
