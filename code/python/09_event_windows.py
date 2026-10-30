import argparse
import io
import os
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

I_SQLDATE, I_A1CC, I_A2CC, I_GOLD, I_TONE = 1, 7, 17, 30, 34
NODES = {
    "2016-11-08 美国大选": ("20161101", "20161115", "20161018", "20161031"),
    "2018-06-15 关税宣布": ("20180608", "20180622", "20180525", "20180607"),
    "2022-10-07 芯片管制": ("20220930", "20221014", "20220916", "20220929"),
    "2023-03-23 TikTok听证": ("20230316", "20230330", "20230302", "20230315")
}


def parse_day(path):
    filedate = os.path.basename(path)[:8]
    records = []
    try:
        with zipfile.ZipFile(path) as archive:
            with archive.open(archive.namelist()[0]) as stream:
                for raw in io.TextIOWrapper(stream, encoding="utf-8", errors="replace"):
                    columns = raw.rstrip("\n").split("\t")
                    if len(columns) != 58:
                        continue
                    records.append((columns[I_SQLDATE], columns[I_A1CC], columns[I_A2CC],
                                    columns[I_GOLD], columns[I_TONE]))
    except Exception as exc:
        return filedate, [], repr(exc)
    return filedate, records, None


def mean(values):
    return round(sum(values) / len(values), 3) if values else None


def window_stats(raw_dir, low, high, workers):
    start = date(int(low[:4]), int(low[4:6]), int(low[6:]))
    end = date(int(high[:4]), int(high[4:6]), int(high[6:]))
    by_name = {}
    for filename in os.listdir(raw_dir):
        if len(filename) >= 12 and filename[8:20] == ".export.CSV.":
            by_name.setdefault(filename[:8], os.path.join(raw_dir, filename))
    files = []
    current = start
    while current <= end:
        key = current.strftime("%Y%m%d")
        if key in by_name:
            files.append(by_name[key])
        current += timedelta(days=1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(parse_day, files))
    n = 0
    us_n = 0
    us_tone = []
    us_gold = []
    us_china_tone = []
    china_tone = []
    targets = Counter()
    for filedate, records, error in results:
        if error:
            print(f"{filedate}: {error}")
        for sqldate, actor1, actor2, gold, tone in records:
            if not low <= sqldate <= high:
                continue
            n += 1
            try:
                tone_value = float(tone)
            except Exception:
                tone_value = None
            try:
                gold_value = float(gold)
            except Exception:
                gold_value = None
            if actor1 == "USA" or actor2 == "USA":
                us_n += 1
                if tone_value is not None:
                    us_tone.append(tone_value)
                if gold_value is not None:
                    us_gold.append(gold_value)
                if actor1 == "USA" and actor2:
                    targets[actor2] += 1
                if (actor1 == "USA" and actor2 == "CHN") or (actor1 == "CHN" and actor2 == "USA"):
                    if tone_value is not None:
                        us_china_tone.append(tone_value)
            if actor1 == "CHN" or actor2 == "CHN":
                if tone_value is not None:
                    china_tone.append(tone_value)
    return {"days": len(files), "events": n, "us_events": us_n,
            "us_share_pct": round(us_n / n * 100, 2) if n else None,
            "us_tone": mean(us_tone), "us_goldstein": mean(us_gold),
            "us_chn_dyad_tone": mean(us_china_tone), "us_chn_dyad_n": len(us_china_tone),
            "chn_tone": mean(china_tone), "us_top_targets": targets.most_common(8)}


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output-dir", default=str(root / "data" / "analysis"))
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    lines = []
    for name, (low, high, baseline_low, baseline_high) in NODES.items():
        window = window_stats(args.raw_dir, low, high, args.workers)
        baseline = window_stats(args.raw_dir, baseline_low, baseline_high, args.workers)
        lines.append(f"=== {name} ===")
        lines.append(f"窗口 {low}~{high}（{window['days']} 天，{window['events']:,} 事件）｜"
                     f"基线 {baseline_low}~{baseline_high}（{baseline['events']:,} 事件）")
        lines.append(f"涉美份额: 窗口 {window['us_share_pct']}% vs 基线 {baseline['us_share_pct']}%")
        lines.append(f"涉美 tone: 窗口 {window['us_tone']} vs 基线 {baseline['us_tone']}｜"
                     f"Goldstein: {window['us_goldstein']} vs 基线 {baseline['us_goldstein']}")
        lines.append(f"美中双边 tone: 窗口 {window['us_chn_dyad_tone']}（n={window['us_chn_dyad_n']:,}）"
                     f" vs 基线 {baseline['us_chn_dyad_tone']}（n={baseline['us_chn_dyad_n']:,}）")
        lines.append(f"涉华 tone: 窗口 {window['chn_tone']} vs 基线 {baseline['chn_tone']}")
        lines.append(f"美国指向最多的对象国: {window['us_top_targets']}")
        lines.append("")
    text = "\n".join(lines)
    with open(os.path.join(args.output_dir, "e11_event_windows.txt"), "w", encoding="utf-8") as stream:
        stream.write(text)
    print(text)


if __name__ == "__main__":
    main()
