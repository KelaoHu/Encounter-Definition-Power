# 原始 GDELT 数据放置说明

本目录不附带原始 ZIP。原始数据由论文作者从 [GDELT 官方网站](https://www.gdeltproject.org/data.html)下载，官方事件文件入口为 [GDELT Events](https://data.gdeltproject.org/events/)。

## 数据规格

- 文件名：`YYYYMMDD.export.CSV.zip`
- 格式：ZIP 内含制表符分隔的 GDELT 2.0 事件文件，共 58 个字段
- 本地原始包：4,727 个按日 ZIP，46.3 GB
- 实测覆盖：2013-04-01—2025-12-31
- 解压后规模：约 40 亿行级原始记录

将原始 ZIP 直接放在一个目录中，不要把不同年份的文件改成其他命名格式。运行时通过 `--raw-dir` 指向该目录，无需把文件复制进仓库。

## 单月处理

```bash
python code/python/01_build_daily.py --raw-dir "/path/to/GDELT/ZIP" --month 202303 --output-dir data/rebuilt
```

## 全量处理

```bash
python code/python/01_build_daily.py --raw-dir "/path/to/GDELT/ZIP" --output-dir data/rebuilt
```

脚本按文件名日期去重，按 `GLOBALEVENTID` 在月内去重，按 `SQLDATE` 归属月份，并剔除早于文件日期 92 天以上的陈旧回填记录。`months_done.txt` 用于断点续跑；如需完全重算，请使用新的空输出目录。

原始包存在重复文件、缺日和历史回填。2025 年 6 月实际只有 13 个日文件。月度序列用于论文分析前已按既定规则处理，但缺失月份仍应在解释时保留敏感性意识。

`data/raw/*.zip` 已加入 `.gitignore`，避免误上传大体积原始文件。
