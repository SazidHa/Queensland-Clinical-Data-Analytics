# Emergency Department Quarterly Data — Fabric Analytics

## Objective
Develop a reproducible Microsoft Fabric data pipeline for Queensland hospital emergency department quarterly performance reporting, with a focus on clear clinical indicator definitions, data quality and traceability.

## Completed exploration
- Created a Fabric Trial workspace and Lakehouse `lh_clinical_operations`.
- Uploaded source files to `Files/ed_raw` in the Lakehouse.
- Inspected the December 2023 file: 630 rows, 16 columns, 105 facility codes, six triage groupings (1–5 and `ALL`).
- Examined Toowoomba Hospital's December 2023 data: 16,872 ED attendances in the `ALL` row; 60% reported as seen within clinically recommended times, with a median wait of 21 minutes.
- Profiled missing values in December 2023: 45 missing values in `Admissions to hospital within 4 hours (%)`, including 30 in triage category 1; five other percentage indicators had 15 missing values each.
- Reviewed CSV schemas across quarters and found differences in column names and field presence.
- Excluded Sep 2022 from the initial combination because its CSV has no header (recoverable in a later iteration).
- Harmonised 11 quarterly CSVs (Mar 2023–Sep 2025) into a Spark DataFrame with 6,930 rows and 17 columns (16 source columns plus `source_file`).

## Source schema changes
| Period | Observation | Harmonisation approach |
| --- | --- | --- |
| Mar 2023–Mar 2024 | 16-column schema | Reference column structure |
| Jun–Sep 2024 | `Median Wait Traffic Light` absent | Set to NULL |
| Dec 2024–Sep 2025 | `Triage_Category` replaces `Triage Category`; traffic-light field absent | Rename and set missing field to NULL |
| Sep 2022 | Headerless, 15-column CSV | Excluded from v1; pending validation |

Note: Schema matching does **not** establish that clinical measures are comparable across time. Indicator definitions require separate validation against publisher documentation.

## Architecture and status
```text
Queensland Government open-data CSVs
        |
        v
Fabric Lakehouse Files/ed_raw      [completed]
        |
        v
PySpark profiling + harmonisation  [completed]
        |
        v
Bronze Delta table                 [pending confirmation]
        |
        v
Silver validated tables            [planned]
        |
        v
Gold clinical KPIs -> Power BI     [planned]
```

The Bronze table is intended to retain source values as strings, harmonise names, and include `source_file` for lineage. Never interpret missing clinical values as zero without evidence.

## Running the notebook
1. Create/choose a Fabric-enabled workspace and attach a default Lakehouse.
2. Download the relevant public CSV files into the Lakehouse folder `Files/ed_raw`.
3. Import and run `notebooks/nb_01_ed_data_exploration.py` as a Fabric notebook or paste its cells into one.
4. Confirm duplicate keys and source definitions before promoting results to analytic layers.

## Current limitations
- No patient-level records are used.
- Bronze write success is not yet confirmed in this README; run the verification code after writing.
- Source values are initially read as strings; suppression tokens and missing values have not yet been fully interpreted.
- `ALL` is a summary group and must not be summed with triage groups 1–5.
- Rates and medians must not be directly summed or averaged across facilities without checking denominators and definitions.

## Source and attribution
[Queensland Government — Emergency departments quarterly data](https://www.data.qld.gov.au/dataset/emergency-departments-quarterly-data). Record downloaded file versions and access date separately. This project is independent of Queensland Health.
