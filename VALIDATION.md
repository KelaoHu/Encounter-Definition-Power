<h1 align="center">Validation of Paper Values and Data Coding Basis</h1>

<p align="center">
  <a href="README.md">← README</a> ·
  <b>English</b> ·
  <a href="VALIDATION.zh-CN.md">简体中文</a>
</p>

---

This file records the verification results between the submitted paper *The Power to Define Encounter: A Century of U.S. International Communication and Its Datafied Form* and the data in this repository. The verification does not modify the original paper, nor does it replace the submitted version with the strict version.

Machine-readable results are in [`data/validation/numerical_checks.csv`](data/validation/numerical_checks.csv), 76 items. The strict version uniformly uses the 25 regional aggregate codes in the official GDELT [CAMEO Country Codes](https://www.gdeltproject.org/data/lookups/CAMEO.country.txt) table and re-aggregates from `visibility_daily.csv`.

## Verdict Categories

- **Consistent** (一致): the paper value and the recomputed value are identical, or the difference comes only from normal display precision.
- **Explainable** (可解释): the paper value can be reproduced, but the definition of the window, the set of region codes, or "unique code" must be stated in full.
- **Strict basis** (严格口径): supplementary results obtained with the complete official region-code table, used for later revision.
- **Reproduction limit** (复现限制): the available material is not sufficient to rebuild the original generation process exactly, or the result involves manual classification.

The machine-readable file also uses two further labels: 补充口径 (supplementary) and 人工归类 (manual coding).

## Totals, Windows, and Data Quality

| Item | Paper value | Recomputed value | Verdict |
|---|---:|---:|---|
| Months in the full window | 153 | 153 | Consistent |
| Events in the full window | 641,360,876 | 641,360,876 | Consistent |
| Months in the clean window | 130 | 130 | Consistent |
| Events in the clean window | about 559 million | 558,518,243 | Consistent |
| Daily files in 2025-06 | 13 | 13 | Consistent |
| U.S. tone, 2015-01 | +2.48 | 2.479652 | Consistent |
| U.S. tone, 2015-02 | +0.58 | 0.576427 | Consistent |
| U.S. tone, 2015-03 | −1.87 | −1.867296 | Consistent |

## E1 Visibility Multiplier

All submitted values can be reproduced from `data/analysis/e1_visibility_multiplier.csv`. The United States is 7.19, Israel 25.57, Palestine 19.56, India 0.10, and China 0.19; the G7 obtains about 43.9% of mentions with about 9.9% of population, and the seven Southern countries obtain about 7.6% of mentions with about 31.8% of population.

The strict version recomputes after removing the official 25 region codes from the daily table:

| Indicator | Submitted version | Strict version |
|---|---:|---:|
| United States | 7.19 | 7.212684 |
| Israel | 25.57 | 25.663028 |
| Palestine | 19.56 | 19.632610 |
| India | 0.10 | 0.102605 |
| China | 0.19 | 0.193754 |
| G7 mention share | 43.9% | 44.081004% |
| Seven Southern countries mention share | 7.6% | 7.659568% |

The difference comes from the treatment of region codes in the denominator and does not change the order-of-magnitude differences between countries.

## E2 Actor Coding Attribution Rate

### Single-Day Sample

The raw file is `20230301.export.CSV.zip`, with 117,093 events in total.

| Definition | Numerator | Share |
|---|---:|---:|
| Both actor country slots empty | 29,046 | 24.805923% |
| Eight core region codes; all non-empty codes are region codes | 1,729 | 1.476604% |
| Eight core region codes; only one non-empty slot and it is a region code | 1,646 | 1.405720% |
| Official 25 region codes; only one non-empty slot and it is a region code | 1,735 | 1.481728% |

The paper's 1.4% corresponds to the third row. "Unique code" here does not mean "all non-empty codes are region codes" but "exactly one non-empty actor country slot". The value can therefore be reproduced, but the text would be clearer if it stated this definition.

### Full-Window Region Slots

| Window and definition | Recomputed share | Relation to the paper |
|---|---:|---|
| 153 months, official 25 region codes, all actor slots as denominator | 3.423623% | corresponds to the paper's 3.42% |
| 130 months, official 25 region codes, all actor slots as denominator | 3.448013% | supplementary |
| 130 months, eight core region codes, all actor slots as denominator | 3.254128% | supplementary |

So the paper's 3.42% corresponds to the full 153 months, not the clean 130 months. The two rates in E2 use different windows and region-code sets: an explainable difference in basis that needs to be labelled clearly.

## E3, E4, E5 Peaks and Composition Effects

### Paper Version Recomputation

The peak months and shares listed in the paper match the existing output: Afghanistan 2021-08, Ukraine 2022-03, North Korea 2018-06, the Taiwan region 2022-08, Iran 2020-01, Venezuela 2019-02, Saudi Arabia 2018-10, the United States 2021-01, and Israel and Palestine 2023-10.

The submitted full sample has 203 entities, a median deviation of −0.07, 162 entities within ±1.7 percentage points, and 13 entities above the band; the deviations of the ten cases also match the paper.

### Note on Region Codes

Among the 203 entities in the submitted version, eight regional aggregate entities remain: `SEA`, `NMR`, `WAF`, `PGS`, `SAF`, `CRB`, `CAS`, and `EAF`. "Countries, territories, and regional entities" is therefore the more accurate name; "sovereign countries after removing all CAMEO regional aggregate codes" would be inaccurate.

### Strict Recomputation from the Daily Table

| Indicator | Submitted version | Strict version |
|---|---:|---:|
| Entities | 203 | 195 |
| Entities within the band | 162 | 156 |
| Share within the band | 79.8% | 80.0% |
| Entities above the band | 13 | 12 |
| Median deviation | −0.07 | −0.081594 |
| Minimum deviation | −6.29 | −6.333944 |
| Maximum deviation | +4.11 | +4.127879 |

The peak months of the ten cases in the strict version are unchanged. Cases sharing the same month — Ukraine, Israel, Palestine, and others — still share the corresponding deviation, and negative extremes remain concentrated in 2022-03 and 2023-10. The main conclusions do not change under the strict basis.

The strict version is not a simple row deletion from the old CSV: it first removes the official 25 region codes, then recomputes monthly denominators, peaks, U.S. shares, and baseline deviations.

## E6, E7 Tone by Relationship Group

| Indicator | Paper value | Recomputed value | Verdict |
|---|---:|---:|---|
| Allies, full-period mean | −1.389 | −1.388930 | Consistent |
| Adversaries, full-period mean | −2.208 | −2.207579 | Consistent |
| Third group, full-period mean | −1.757 | −1.757324 | Consistent |
| Adversaries below allies | over 99% | 129/130 | Consistent |
| Minimum annual gap | 0.27 | 0.270643 | Consistent |
| Maximum annual gap | 1.49 | 1.491313 | Consistent |

The full-period ally–adversary gap is 0.818648. The group definitions, monthly weighting, and Chow test output in the existing scripts are retained.

## E8 Representation and Behaviour Coding

The clean window is 2015-03 to 2025-12 in all cases.

| Series and breakpoint | Paper F | Recomputed F | Verdict |
|---|---:|---:|---|
| U.S.-related share, 2016-01 | 13.4 | 13.363983 | Consistent |
| Conflict share, 2016-01 | 8.6 | 8.644909 | Consistent |
| Goldstein, 2016-01 | 3.1 | 3.125098 | Consistent |
| Tone, 2017-07 | 41.3 | 41.256583 | Consistent |

Before and after the U.S.-related share breakpoint the means are 16.7516% and 17.7464%, consistent with the paper's 16.8% and 17.8%. For the either-party series the means are 28.6670% and 30.3269%.

The BIC-optimal model for the either-party series contains three breakpoints: 2016-03, 2020-02, and 2021-11. The 2016-03 mentioned in the paper is indeed in the optimal model, but it is not the only breakpoint.

### AR(1)-GLS Reproduction Limit

No script generating the paper's exact AR(1)-GLS results was found in the original directory. Using an AR(1) error model with `nlme::gls` gives p=0.1083 for the U.S.-related share and p=0.0281 for the conflict share at 2016-01; another iterative GLSAR implementation gives p=0.0882 and p=0.0235. Neither reproduces the paper's 0.19 and 0.035 exactly, but both keep the direction: the U.S.-related share is not significant, while the conflict share is.

The repository therefore retains the paper's statement about model dependence but does not claim to have reproduced these two p values exactly.

## E9 Source Composition

The March 2023 raw files contain 3,534,065 events, of which 964,227 are U.S.-related, or 27.3%. The displayed shares of the top 30 source domains sum to 18.73%, matching the paper's 18.7%.

The statement that "28 belong to U.S. or British media" rests on manual classification by headquarters location; it is not a fully automatic computation. The repository retains the raw domain counts and the existing classification code, but has not independently rechecked the headquarters of every outlet.

## E10 U.S. Events toward China

| Item | Paper value | Recomputed value | Verdict |
|---|---:|---:|---|
| Chow F, 2017-07 | 49.1 | 49.090982 | Consistent |
| Chow F, 2018-06 | 69.9 | 69.943300 | Consistent |
| BIC-selected breakpoint | 2018-06 | 2018-06 | Consistent |

The monthly series `us_china_tone_monthly.csv` is included and supports these recomputations. The original event-level generation script was not found in the original directory, so rebuilding this monthly series from the raw ZIPs is outside the current scope of full reproduction.

## E11 Thick Description of Nodes

| Item | Paper value | Recomputed value | Verdict |
|---|---:|---:|---|
| U.S.-related share in the 2016 election week | 30.7% | 30.72% | Consistent |
| Preceding baseline | 27.5% | 27.54% | Consistent |
| U.S.–China bilateral events in the 2023 hearing week | 9,010 | 9,010 | Consistent |
| Preceding baseline | 5,593 | 5,593 | Consistent |
| Increase | 61% | 61.0942% | Consistent |

E11 counts events without event-level deduplication; the difference from the monthly series is explained in the README.

## E12 Sensitivity to the Missing Month

After excluding 2025-06:

| Item | Paper value | Recomputed value | Verdict |
|---|---:|---:|---|
| U.S.-related share Chow F | 13.2 | 13.201009 | Consistent |
| Tone Chow F | 42.3 | 42.318037 | Consistent |

Conclusions are unchanged after handling the missing month.

## Sync Checklist for Future Revisions

If the complete official region-code basis is adopted later, update:

1. Figure 1 and Appendix E1: small changes in the U.S. multiplier, the G7 and seven-Southern-country mention shares.
2. Figure 2 and Appendix E3–E5: 203 to 195, 162 to 156, 13 to 12, 79.8% to 80.0%, median to −0.08; the distribution and case values inside the figure need re-export.
3. The "sovereign country basis" wording in the text: if the submitted version is kept, change it to "countries, territories, and regional entities"; only if the strict version is adopted may it be described as removing all official regional aggregate codes.
4. The E2 table note: state the eight region codes and the unique non-empty slot definition for the single-day 1.4%, and the 153-month window and official 25 region codes for 3.42%.
5. E8 robustness: if the exact AR(1)-GLS p values are to be made public, add the software package, the model specification, and the generating code.

These are options for later revision only; this preparation did not change the paper text or the submitted figures.
