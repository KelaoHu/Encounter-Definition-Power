import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd


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
                start = min_seg * (k - 1)
                for i in range(start, j - min_seg + 1):
                    value = costs[i, k - 1] + segment_sse(i, j)
                    if value < costs[j, k]:
                        costs[j, k] = value
                        parents[j, k] = i
        return costs[n, segments], parents

    results = []
    for segments in range(1, max_breaks + 2):
        sse, parents = dp(segments)
        bic = n * np.log(sse / n) + (2 * segments) * np.log(n)
        breaks = []
        j = n
        k = segments
        while k > 1:
            i = parents[j, k]
            breaks.append(i)
            j = i
            k -= 1
        results.append((sorted(breaks), bic, sse))
    return min(results, key=lambda item: item[1]), results


def chow(values, break_index):
    values = np.asarray(values, dtype=float)
    n = len(values)
    sse0 = ((values - values.mean()) ** 2).sum()
    sse1 = ((values[:break_index] - values[:break_index].mean()) ** 2).sum()
    sse1 += ((values[break_index:] - values[break_index:].mean()) ** 2).sum()
    return (sse0 - sse1) / (sse1 / (n - 2))


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=str(root / "data" / "processed"))
    parser.add_argument("--output-dir", default=str(root / "data" / "processed"))
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    us = pd.read_csv(os.path.join(args.input_dir, "us_index_daily.csv"), dtype={"date": str})
    us["month"] = us["date"].str[:6]
    monthly = pd.DataFrame({"us_a1": us.groupby("month")["us_a1"].sum(),
                            "us_a2": us.groupby("month")["us_a2"].sum()})
    grouped = us.groupby("month").apply(lambda frame: pd.Series({
        "goldstein": np.average(frame["goldstein_mean"].fillna(0), weights=frame["us_a1"] + frame["us_a2"])
        if (frame["us_a1"] + frame["us_a2"]).sum() > 0 else np.nan,
        "tone": np.average(frame["tone_mean"].fillna(0), weights=frame["us_a1"] + frame["us_a2"])
        if (frame["us_a1"] + frame["us_a2"]).sum() > 0 else np.nan
    }), include_groups=False)
    monthly = monthly.join(grouped)
    global_counts = {}
    with open(os.path.join(args.input_dir, "months_done.txt"), encoding="utf-8") as stream:
        for line in stream:
            parts = line.split("\t")
            global_counts[parts[0]] = int(parts[1])
    monthly["global_n"] = pd.Series(global_counts)
    monthly["us_share"] = monthly["us_a1"] / monthly["global_n"]
    monthly["us_share2"] = (monthly["us_a1"] + monthly["us_a2"]) / monthly["global_n"]
    monthly = monthly.reset_index().sort_values("month").reset_index(drop=True)
    monthly.to_csv(os.path.join(args.output_dir, "monthly_summary.csv"), index=False, encoding="utf-8-sig")
    months = monthly["month"].tolist()
    series = {"us_share": monthly["us_share"].values,
              "goldstein": monthly["goldstein"].values,
              "tone": monthly["tone"].values}
    lines = [f"样本: {months[0]}–{months[-1]} (n={len(months)}个月)", ""]
    for name, values in series.items():
        mask = ~np.isnan(values)
        clean = values[mask]
        clean_months = [month for month, keep in zip(months, mask) if keep]
        (breaks, bic, sse), _ = bp_detect(clean)
        statistic = chow(clean, clean_months.index("201601"))
        lines.append(f"【{name}】")
        lines.append(f"  假设断点2016-01 Chow F = {statistic:.2f}")
        lines.append(f"  BIC最优断点数: {len(breaks)}")
        for index in breaks:
            if index < len(clean_months):
                lines.append(f"    断点 @ {clean_months[index]}")
        lines.append("")
    output_text = os.path.join(args.output_dir, "breakpoints.txt")
    with open(output_text, "w", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
