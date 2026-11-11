# Queensland Clinical Data Analytics — Source-to-Target Schema Mapping

## Scope and status

This document maps fields from **Queensland Health quarterly ED CSVs** to `bronze_ed_quarterly`, then to `silver_ed_quarterly`, and describes their known downstream Gold uses. It is based on the Bronze and Silver notebook code reviewed for this project.

**Mapping confidence:** Bronze renaming and Silver conversion expressions below are **confirmed from shared notebook code**. Detailed Gold `select`, `filter`, and aggregation expressions **must be verified against `Notebook_1nb_03_ed_gold_analytics`** before treating the Gold mapping as a formal specification. No unverified Gold calculations are invented here.

### Record grain

- **Source/Bronze/Silver:** facility/HHS code × reporting quarter × triage category (`1`–`5` and `ALL`), with `source_file` recording origin.
- **Gold hospital:** facility/HHS code × quarter; 1,155 rows across 11 quarters and 105 reporting facility/HHS codes.
- **Gold triage:** facility/HHS code × quarter × triage category `1`–`5`; 5,775 rows.
- **Important:** `ALL` is an aggregate total; do not add its attendance count to categories `1`–`5`.

## Source CSV → Bronze → Silver field mapping

The Bronze ingestion reads files using `header=true`, `inferSchema=false` and preserves fields initially as strings. The September 2022 file `open-data-ed_quarterly1sep22.csv` is explicitly excluded in the initial ingestion configuration.

| Original CSV column | Bronze column | Silver conversion / standardisation | Type or format after Silver | Downstream analytical role |
|---|---|---|---|---|
| `Facility/HHS Code` | `facility_code` | `try_cast(... AS INT)` | Integer | Facility/HHS identifier and dimensional relationships |
| `Facility/HHS Desc` | `facility_name` | No conversion shown | String | Facility label / benchmarking |
| `Last Month in QTR` | `reporting_quarter` | Original field retained; also derive `quarter_end_month` using date parsing | Original string; derived date | Reporting-period grouping and sorting |
| `Triage Category` / `Triage_Category` | `triage_category` | Harmonise header in Bronze; `upper(trim(...))` in Silver | String (`1`–`5`, `ALL` expected) | Distinguishes hospital aggregate from individual triage groups |
| `Number of Attendances` | `number_of_attendances` | `try_cast(... AS INT)` | Integer | ED demand and attendance totals |
| `Variation in the number of attendances (%)` | `attendance_variation_pct` | `try_cast(trim(...) AS DOUBLE)` | Double | Quarterly attendance variation |
| `Patients Seen within clinically recommended times (%)` | `seen_within_target_pct` | `try_cast(trim(...) AS DOUBLE)` | Double | Triage treatment timeliness |
| `Median Waiting time to treatment (minutes)` | `median_wait_minutes` | `try_cast(trim(...) AS DOUBLE)` | Double | Waiting-time indicator; **not a percentage** |
| `Patients who did not wait for treatment (%)` | `did_not_wait_pct` | `try_cast(trim(...) AS DOUBLE)` | Double | Did-not-wait rate |
| `Patients admitted from the Emergency Department (%)` | `admitted_from_ed_pct` | `try_cast(trim(...) AS DOUBLE)` | Double | Admission proportion |
| `Admissions to hospital within 4 hours (%)` | `admissions_within_4h_pct` | `try_cast(trim(...) AS DOUBLE)` | Double | Admission timeliness |
| `Patients whose ED stay was within 4 hours (%)` | `ed_stay_within_4h_pct` | `try_cast(trim(...) AS DOUBLE)` | Double | Four-hour ED stay indicator |
| `Number of patients who left after treatment commenced` | `left_after_treatment_count` | `try_cast(... AS INT)` | Integer | Left-after-treatment count |
| `Percentage of patients who left after treatment commenced (%)` | `left_after_treatment_pct` | `try_cast(trim(...) AS DOUBLE)` | Double | Left-after-treatment rate |
| `Number of patients who did not wait for treatment` | `did_not_wait_count` | `try_cast(... AS INT)` | Integer | Did-not-wait count |
| `Median Wait Traffic Light` | `median_wait_traffic_light` | Missing source column created as `NULL` string in Bronze; no Silver conversion shown | String / nullable | Source categorical indicator when available |
| *(derived from filename)* | `source_file` | `lit(file.name)` added in Bronze; retained in Silver unless later code changes it | String | Source-file lineage |

### Derived Silver date field

| Silver field | Input | Actual expression | Interpretation |
|---|---|---|---|
| `quarter_end_month` | `reporting_quarter` (e.g. `Dec-23`) | `to_date(initcap(trim(reporting_quarter)), 'MMM-yy')` | First day of reporting quarter's final month (`2023-12-01` for `Dec-23`), **not** the calendar quarter-end date |

## Confirmed Bronze processing rules

1. Discover `.csv` files dynamically from `Files/ed_raw`, except configured exclusions.
2. Read original CSV values as strings with column headers.
3. Rename source `Triage_Category` to `Triage Category` where encountered.
4. Add `Median Wait Traffic Light` as `NULL` string where the entire source column is absent.
5. Validate the harmonised source-column set against `reference_columns`; raise `ValueError` for missing or extra fields.
6. Select reference columns in a consistent order and append `source_file`.
7. Combine datasets using `reduce(lambda a, b: a.unionByName(b), dataframes)`.
8. Rename raw headers to the Bronze names in the table above and save `bronze_ed_quarterly` as Delta.

**Bronze baseline:** 11 included files, 6,930 records and 17 columns (16 source fields plus `source_file`).

## Confirmed Silver processing rules

```python
# Integer columns
integer_columns = [
    "facility_code",
    "number_of_attendances",
    "left_after_treatment_count",
    "did_not_wait_count",
]

# Double columns
numeric_columns = [
    "attendance_variation_pct",
    "seen_within_target_pct",
    "median_wait_minutes",
    "did_not_wait_pct",
    "admitted_from_ed_pct",
    "admissions_within_4h_pct",
    "ed_stay_within_4h_pct",
    "left_after_treatment_pct",
]
```

- Integer conversion uses `try_cast(column AS INT)`.
- Numeric conversion uses `try_cast(trim(column) AS DOUBLE)`.
- Reporting-month date is derived with `to_date(initcap(trim(reporting_quarter)), 'MMM-yy')`.
- Triage label is standardised with `upper(trim(triage_category))`.
- Failed `try_cast` operations can return `NULL`. Numeric-conversion validation has been added; reported unexpected failures were **0**, subject to the accepted missing-marker definition.

**Silver baseline:** 6,930 rows. A row-count match does not on its own prove value-level reconciliation.

## Gold mapping — known grain and intended use

| Output | Known record level | Main inputs / fields | Verification required |
|---|---|---|---|
| `gold_ed_hospital_quarterly` | Facility/HHS × quarter | Hospital-level attendances, recommended-time %, waiting-time and four-hour metrics; logically uses `ALL` grain | Confirm actual filter and selected columns in Notebook 3 |
| `gold_ed_triage_performance` | Facility/HHS × quarter × triage 1–5 | `triage_category`, `number_of_attendances`, `seen_within_target_pct`, `median_wait_minutes` and relevant identifiers | Confirm actual filter and derived columns in Notebook 3 |
| `gold_ed_hospital_comparison` | Selected six reporting facilities, selected period | Hospital quarterly KPIs | Confirm selection criteria and columns in Notebook 3 |
| `dim_facility` | Facility/HHS reference | `facility_code`, `facility_name` | Confirm key, distinctness and fields in Notebook 3 |
| `dim_quarter` | Reporting period reference | `reporting_quarter`, `quarter_end_month` | Confirm key and derived fields in Notebook 3 |

**Gold-level validity:** Preserve the distinction between `ALL` and individual triage categories. Hospital rates/medians should not be recalculated by blindly summing or averaging category-level rates and medians. Refer to published aggregate `ALL` metrics or use suitable denominators and documented calculation rules.

## Data quality and reconciliation matrix

| Quality control | Stage | What it tests | Current known status |
|---|---|---|---|
| Expected source schema / unexpected headers | Bronze | Structure before union | Implemented as blocking `ValueError` |
| Facility-quarter-triage duplicate key | Bronze / quality notebook | Multiple rows with same business key | Zero duplicate groups observed; whether Bronze stage now blocks on duplicates must be verified |
| Non-numeric values / conversion failure | Silver | Values that cannot be cast into target types | Updated diagnostic reported zero **unexpected** failures under configured missing-marker policy |
| KPI percentage ranges | Quality notebook | Percentages within expected limits | PASS in recorded run |
| Missing clinical indicators | Quality notebook | Null / unavailable indicators | Warnings observed for eight clinical indicators |
| Attendance reconciliation | Quality notebook | Sum of triage 1–5 vs reported `ALL` totals | PASS in recorded run |
| Full source CSV → persisted Bronze value comparison | Proposed | Original records versus saved records | **Not yet independently implemented and verified** |
| Full Bronze → persisted Silver expected-value comparison | Proposed | Converted values preserve meaning and match intended transformation | **Not yet independently implemented and verified** |
| Silver → Gold field-level calculation and aggregation audit | Proposed | Gold values match documented business rules | **Requires mapping against actual Gold notebook code** |

## Recommended implementation of full source-to-target checks

1. Validate source-file counts and source keys per filename.
2. Re-read original CSVs independently, harmonising only documented header differences.
3. Compare complete expected raw-source rows with persisted Bronze values using column-aligned, duplicate-aware comparisons such as `exceptAll()` in both directions.
4. Compare Bronze-derived *expected* Silver values with persisted Silver values (not Silver with itself), including null-safe comparisons and explicit checks for new nulls.
5. Block downstream publishing when critical reconciliation mismatches occur; persist audit statistics and mismatched record samples with appropriate safeguards.

This proposed reconciliation is separate from tests that determine whether a source's published clinical values are themselves factually accurate.

## Related document

See [`architecture/medallion-architecture.md`](architecture/medallion-architecture.md) for the Fabric workflow and Mermaid architecture diagram.
