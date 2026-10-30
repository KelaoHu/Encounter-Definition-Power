import argparse
import os
from pathlib import Path

import pandas as pd

CLEAN_START = "20150301"
MIN_EVENTS = 20000
REGION_CODES = {"AFR", "ASA", "BLK", "EUR", "LAM", "MEA", "NAC", "SAS", "WST",
                "EEU", "CAU", "NAF", "SAM", "SCN"}
G7 = ["USA", "JPN", "DEU", "FRA", "GBR", "ITA", "CAN"]
SOUTH7 = ["IND", "IDN", "BRA", "PAK", "NGA", "EGY", "ZAF"]


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
    rows = []
    for country, frame in monthly.groupby("country"):
        if frame["n_events"].sum() < MIN_EVENTS:
            continue
        top = frame.sort_values("share", ascending=False).head(3)
        rows.append({"country": country, "total_events": int(frame["n_events"].sum()),
                     "peak1": f"{top.iloc[0]['month']}:{top.iloc[0]['share']:.2f}%",
                     "peak2": f"{top.iloc[1]['month']}:{top.iloc[1]['share']:.2f}%",
                     "peak3": f"{top.iloc[2]['month']}:{top.iloc[2]['share']:.2f}%"})
    peaks = pd.DataFrame(rows).sort_values("total_events", ascending=False)
    peaks.to_csv(os.path.join(args.output_dir, "e3_peak_months.csv"), index=False, encoding="utf-8-sig")
    population = pd.read_csv(os.path.join(args.input_dir, "population_wpp2024_2020.csv"))
    world = float(population.loc[population["country"] == "World", "population"].iloc[0])
    popmap = dict(zip(population["country"], population["population"]))
    aggregate = visibility.groupby("country")["n_events"].sum()
    share = aggregate / aggregate.sum() * 100
    rows = []
    for country, value in popmap.items():
        if country == "World" or country not in share.index:
            continue
        population_share = value / world * 100
        rows.append({"country": country, "mention_share_pct": round(share[country], 3),
                     "population": int(value), "pop_share_pct": round(population_share, 3),
                     "visibility_multiplier": round(share[country] / population_share, 2)})
    multipliers = pd.DataFrame(rows).sort_values("visibility_multiplier", ascending=False)
    multipliers.to_csv(os.path.join(args.output_dir, "e1_visibility_multiplier.csv"), index=False, encoding="utf-8-sig")
    print(f"峰值表：{len(peaks)} 个实体")
    for name, codes in [("G7", G7), ("南方七国", SOUTH7)]:
        mention = share[share.index.isin(codes)].sum()
        population_share = sum(popmap[country] for country in codes) / world * 100
        print(f"{name}：人口份额 {population_share:.2f}%｜提及份额 {mention:.2f}%｜倍率 {mention / population_share:.2f}")


if __name__ == "__main__":
    main()
