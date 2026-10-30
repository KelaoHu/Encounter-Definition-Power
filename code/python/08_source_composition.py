import argparse
import collections
import csv
import os
import re
import zipfile
from pathlib import Path

US_UK_MEDIA = {"nytimes.com", "washingtonpost.com", "cnn.com", "foxnews.com", "wsj.com", "usatoday.com",
               "apnews.com", "npr.org", "bloomberg.com", "reuters.com", "cnbc.com", "abcnews.go.com",
               "cbsnews.com", "nbcnews.com", "politico.com", "thehill.com", "voanews.com", "stripes.com",
               "defense.gov", "whitehouse.gov", "state.gov", "newsweek.com", "time.com", "nypost.com",
               "usnews.com", "latimes.com", "forbes.com", "businessinsider.com", "axios.com", "yahoo.com",
               "huffpost.com", "theguardian.com", "bbc.com", "bbc.co.uk", "ft.com", "telegraph.co.uk",
               "dailymail.co.uk", "independent.co.uk", "thetimes.co.uk", "scmp.com", "scmp.cn"}
NATIONAL_SUFFIXES = (".cn", ".ru", ".ir", ".kp", ".in", ".br", ".za", ".ng", ".id", ".tr", ".fr", ".de",
                     ".jp", ".kr", ".it", ".es", ".au", ".ca", ".il", ".ps", ".ua", ".sa", ".eg", ".pk",
                     ".mx", ".ar", ".vn", ".th", ".my", ".sg", ".ph", ".ke", ".pl", ".nl", ".be", ".se",
                     ".no", ".ch", ".at", ".gr", ".cz")
GENERIC_SUFFIXES = (".com", ".net", ".org", ".io", ".info", ".news", ".tv", ".me")


def domain_of(url):
    match = re.match(r"https?://([^/]+)", url or "")
    if not match:
        return ""
    domain = match.group(1).lower()
    return domain[4:] if domain.startswith("www.") else domain


def base_domain(domain):
    parts = domain.split(".")
    if len(parts) >= 3 and parts[-2] in ("co", "com", "gov", "org", "ac") and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else domain


def classify(domain):
    if not domain:
        return "other"
    if domain in US_UK_MEDIA:
        return "us_uk_major"
    if domain.endswith((".gov", ".us", ".mil")):
        return "us_uk_major"
    if domain.endswith(NATIONAL_SUFFIXES):
        return "national_domain"
    if domain.endswith(GENERIC_SUFFIXES):
        return "generic_tld"
    return "other"


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--month", default="202303")
    parser.add_argument("--output-dir", default=str(root / "data" / "analysis"))
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    files = sorted(filename for filename in os.listdir(args.raw_dir)
                   if filename.startswith(args.month) and filename.endswith(".zip"))
    total_events = 0
    usa_events = 0
    domains = collections.Counter()
    classes = collections.Counter()
    lines = [f"抽样月份：{args.month}，文件数 {len(files)}"]
    for filename in files:
        with zipfile.ZipFile(os.path.join(args.raw_dir, filename)) as archive:
            with archive.open(archive.namelist()[0]) as stream:
                text = (line.decode("utf-8", "replace") for line in stream)
                for row in csv.reader(text, delimiter="\t"):
                    if len(row) < 58:
                        continue
                    total_events += 1
                    if "USA" in (row[7].upper(), row[17].upper()):
                        usa_events += 1
                        domain = base_domain(domain_of(row[57]))
                        domains[domain] += 1
                        classes[classify(domain)] += 1
    share = usa_events / total_events * 100 if total_events else 0
    lines.append(f"当月事件总数 {total_events:,}；涉美事件 {usa_events:,}（{share:.1f}%）")
    lines.append("=== 涉美事件信源分类份额 ===")
    for category, count in classes.most_common():
        lines.append(f"{category}: {count:,}（{count / usa_events * 100:.1f}%）")
    lines.append("=== 涉美事件前 30 信源域名 ===")
    for domain, count in domains.most_common(30):
        lines.append(f"{domain}\t{count:,}\t{count / usa_events * 100:.2f}%")
    text = "\n".join(lines)
    with open(os.path.join(args.output_dir, "e9_source_composition.txt"), "w", encoding="utf-8") as stream:
        stream.write(text)
    print(text)


if __name__ == "__main__":
    main()
