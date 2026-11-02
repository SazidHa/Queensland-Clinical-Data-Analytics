# Fabric PySpark notebook source (Python cells separated by # CELL).
# Attach lh_clinical_operations as the default Lakehouse before running.

# CELL: Imports and inventory
from notebookutils import fs
from pyspark.sql import functions as F
from functools import reduce

files = fs.ls('Files/ed_raw')
for f in files:
    print(f.name, f.size, 'bytes')

# CELL: Examine the reference quarter
df = spark.read.option('header', True).option('inferSchema', True).csv('Files/ed_raw/ed_hosp-dec23.csv')
print('Rows:', df.count(), 'Columns:', len(df.columns))
df.printSchema()
display(df.limit(10))

# CELL: Missing-value profiling
missing = df.select(*[
    F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c)
    for c in df.columns
])
display(missing)

# CELL: Standardise and combine CSV files
reference_columns = df.columns
exclude = {'open-data-ed_quarterly1sep22.csv'}
source_files = sorted((f for f in fs.ls('Files/ed_raw') if f.name.lower().endswith('.csv') and f.name not in exclude), key=lambda f: f.name)
frames = []
for file in source_files:
    part = spark.read.option('header', 'true').option('inferSchema', 'false').csv(file.path)
    if 'Triage_Category' in part.columns:
        part = part.withColumnRenamed('Triage_Category', 'Triage Category')
    if 'Median Wait Traffic Light' not in part.columns:
        part = part.withColumn('Median Wait Traffic Light', F.lit(None).cast('string'))
    missing_cols = sorted(set(reference_columns) - set(part.columns))
    extra_cols = sorted(set(part.columns) - set(reference_columns))
    if missing_cols or extra_cols:
        raise ValueError(f'{file.name}: missing={missing_cols}, extra={extra_cols}')
    frames.append(part.select(*reference_columns).withColumn('source_file', F.lit(file.name)))
df_combined = reduce(lambda a, b: a.unionByName(b), frames)
print('Files:', len(source_files), 'Rows:', df_combined.count(), 'Columns:', len(df_combined.columns))

# CELL: Check duplicate business keys; investigate nonzero findings before proceeding
duplicates = df_combined.groupBy('Facility/HHS Code', 'Last Month in QTR', 'Triage Category').count().filter(F.col('count') > 1)
print('Duplicate groups:', duplicates.count())
display(duplicates)

# CELL: Delta-safe column names
column_mapping = {
 'Facility/HHS Code': 'facility_code',
 'Facility/HHS Desc': 'facility_name',
 'Last Month in QTR': 'reporting_quarter',
 'Triage Category': 'triage_category',
 'Number of Attendances': 'number_of_attendances',
 'Variation in the number of attendances (%)': 'attendance_variation_pct',
 'Patients Seen within clinically recommended times (%)': 'seen_within_target_pct',
 'Median Waiting time to treatment (minutes)': 'median_wait_minutes',
 'Patients who did not wait for treatment (%)': 'did_not_wait_pct',
 'Patients admitted from the Emergency Department (%)': 'admitted_from_ed_pct',
 'Admissions to hospital within 4 hours (%)': 'admissions_within_4h_pct',
 'Patients whose ED stay was within 4 hours (%)': 'ed_stay_within_4h_pct',
 'Number of patients who left after treatment commenced': 'left_after_treatment_count',
 'Percentage of patients who left after treatment commenced (%)': 'left_after_treatment_pct',
 'Number of patients who did not wait for treatment': 'did_not_wait_count',
 'Median Wait Traffic Light': 'median_wait_traffic_light',
 'source_file': 'source_file'
}
df_bronze = df_combined
for original, clean in column_mapping.items():
    df_bronze = df_bronze.withColumnRenamed(original, clean)

# CELL: Save only after checking duplicates and schema
# df_bronze.write.format('delta').mode('overwrite').saveAsTable('bronze_ed_quarterly')
# result = spark.table('bronze_ed_quarterly')
# print(result.count(), len(result.columns))
