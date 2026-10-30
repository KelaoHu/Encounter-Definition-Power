import argparse
import csv
import io
import os
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

I_ID, I_SQLDATE, I_YEAR, I_A1CC, I_A2CC = 0, 1, 3, 7, 17
I_QUAD, I_GOLD, I_NART, I_TONE = 29, 30, 33, 34
MIN_SQLDATE, MAX_SQLDATE = "20130101", "20251231"
STALE_DAYS = 92


def parse_date(value):
    return datetime.strptime(value, "%Y%m%d").date()


def is_stale(sqldate, filedate):
    return (parse_date(filedate) - parse_date(sqldate)).days > STALE_DAYS


def list_months(raw_dir):
    months = set()
    for filename in os.listdir(raw_dir):
        if len(filename) >= 12 and filename[8:20] == ".export.CSV.":
            months.add(filename[:6])
    return sorted(months)


def parse_file(args):
    path, filedate = args
    events = []
    n_rows = 0
    n_match = 0
    error = None
    try:
        with zipfile.ZipFile(path) as archive:
            with archive.open(archive.namelist()[0]) as stream:
                for raw in io.TextIOWrapper(stream, encoding="utf-8", errors="replace"):
                    columns = raw.rstrip("\n").split("\t")
                    if len(columns) != 58:
                        continue
                    n_rows += 1
                    if columns[I_YEAR] == filedate[:4]:
                        n_match += 1
                    events.append((columns[I_ID], columns[I_SQLDATE], columns[I_A1CC], columns[I_A2CC],
                                   columns[I_QUAD], columns[I_GOLD], columns[I_NART], columns[I_TONE]))
    except Exception as exc:
        error = repr(exc)
    return filedate, events, n_rows, n_match, error


def to_float(value):
    try:
        return float(value)
    except Exception:
        return None


def append_csv(output_dir, name, header, rows):
    path = os.path.join(output_dir, name)
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        if not exists:
            writer.writerow(header)
        writer.writerows(rows)


def process_month(ym, raw_dir, output_dir, workers):
    files = {}
    for filename in os.listdir(raw_dir):
        if filename.startswith(ym) and filename.endswith(".export.CSV.zip"):
            files.setdefault(filename[:8], os.path.join(raw_dir, filename))
    if not files:
        return 0
    tasks = sorted(((path, day) for day, path in files.items()))
    started = datetime.now()
    print(f"[{ym}] {len(tasks)} 个文件开始解析", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(parse_file, tasks))
    best = {}
    audit_rows = []
    for filedate, events, n_rows, n_match, error in results:
        if error:
            print(f"[{ym}] {filedate}: {error}", flush=True)
        pct = n_match / n_rows if n_rows else 0.0
        audit_rows.append((filedate, n_rows, round(pct, 3), "BACKFILL" if n_rows and pct < 0.5 else ""))
        for event in events:
            event_id = event[0]
            current = best.get(event_id)
            if current is None or filedate > current[0]:
                best[event_id] = (filedate, event)
    us = defaultdict(lambda: {"a1": 0, "a2": 0, "gold_sum": 0.0, "gold_n": 0,
                              "tone_sum": 0.0, "tone_n": 0, "q": [0, 0, 0, 0]})
    visibility = defaultdict(lambda: {"n": 0, "art": 0, "tone_sum": 0.0, "tone_n": 0})
    china = defaultdict(lambda: {"a1": 0, "a2": 0, "gold_sum": 0.0, "gold_n": 0,
                                 "tone_sum": 0.0, "tone_n": 0})
    n_events = 0
    n_stale = 0
    n_outmonth = 0
    for filedate, event in best.values():
        _, sqldate, actor1, actor2, quad, gold, n_articles, tone = event
        if not MIN_SQLDATE <= sqldate <= MAX_SQLDATE:
            continue
        if sqldate[:6] != ym:
            n_outmonth += 1
            continue
        if is_stale(sqldate, filedate):
            n_stale += 1
            continue
        n_events += 1
        gold_value = to_float(gold)
        tone_value = to_float(tone)
        try:
            article_count = int(n_articles)
        except Exception:
            article_count = 0
        if actor1 == "USA" or actor2 == "USA":
            daily = us[sqldate]
            if actor1 == "USA":
                daily["a1"] += 1
                try:
                    quad_index = int(quad) - 1
                    if 0 <= quad_index < 4:
                        daily["q"][quad_index] += 1
                except Exception:
                    pass
            if actor2 == "USA":
                daily["a2"] += 1
            if gold_value is not None:
                daily["gold_sum"] += gold_value
                daily["gold_n"] += 1
            if tone_value is not None:
                daily["tone_sum"] += tone_value
                daily["tone_n"] += 1
        for country in (actor1, actor2):
            if country:
                daily = visibility[(sqldate, country)]
                daily["n"] += 1
                daily["art"] += article_count
        if actor2 and actor2 != actor1 and tone_value is not None:
            daily = visibility[(sqldate, actor2)]
            daily["tone_sum"] += tone_value
            daily["tone_n"] += 1
        if actor1 == "CHN" or actor2 == "CHN":
            daily = china[sqldate]
            if actor1 == "CHN":
                daily["a1"] += 1
            if actor2 == "CHN":
                daily["a2"] += 1
            if gold_value is not None:
                daily["gold_sum"] += gold_value
                daily["gold_n"] += 1
            if tone_value is not None:
                daily["tone_sum"] += tone_value
                daily["tone_n"] += 1
    append_csv(output_dir, "us_index_daily.csv",
               ["date", "us_a1", "us_a2", "goldstein_mean", "tone_mean", "q1", "q2", "q3", "q4"],
               ([day, values["a1"], values["a2"],
                 round(values["gold_sum"] / values["gold_n"], 4) if values["gold_n"] else "",
                 round(values["tone_sum"] / values["tone_n"], 4) if values["tone_n"] else "",
                 values["q"][0], values["q"][1], values["q"][2], values["q"][3]]
                for day, values in sorted(us.items())))
    append_csv(output_dir, "visibility_daily.csv",
               ["date", "country", "n_events", "n_articles", "tone_mean"],
               ([day, country, values["n"], values["art"],
                 round(values["tone_sum"] / values["tone_n"], 4) if values["tone_n"] else ""]
                for (day, country), values in sorted(visibility.items())))
    append_csv(output_dir, "china_daily.csv",
               ["date", "chn_a1", "chn_a2", "goldstein_mean", "tone_mean"],
               ([day, values["a1"], values["a2"],
                 round(values["gold_sum"] / values["gold_n"], 4) if values["gold_n"] else "",
                 round(values["tone_sum"] / values["tone_n"], 4) if values["tone_n"] else ""]
                for day, values in sorted(china.items())))
    append_csv(output_dir, "files_audit.csv", ["filedate", "n_rows", "pct_year_match", "flag"], audit_rows)
    with open(os.path.join(output_dir, "months_done.txt"), "a", encoding="utf-8") as stream:
        stream.write(f"{ym}\t{n_events}\tstale_dropped={n_stale}\toutmonth_dropped={n_outmonth}\t{datetime.now() - started}\n")
    print(f"[{ym}] 完成：{n_events:,} 条事件", flush=True)
    return n_events


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output-dir", default=str(root / "data" / "processed"))
    parser.add_argument("--month")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    done_path = os.path.join(args.output_dir, "months_done.txt")
    done = set()
    if os.path.exists(done_path):
        with open(done_path, encoding="utf-8") as stream:
            done = {line.split("\t")[0] for line in stream if line.strip()}
    months = [args.month] if args.month else list_months(args.raw_dir)
    for ym in months:
        if ym in done:
            print(f"[{ym}] 已完成，跳过", flush=True)
            continue
        process_month(ym, args.raw_dir, args.output_dir, args.workers)


if __name__ == "__main__":
    main()
