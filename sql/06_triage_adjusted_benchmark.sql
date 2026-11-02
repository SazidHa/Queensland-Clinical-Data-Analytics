
WITH triage_data AS (
    SELECT
        facility_code,
        facility_name,
        triage_category,
        attendances,
        seen_within_target_pct
    FROM gold_ed_triage_performance
    WHERE quarter_end_month = '2025-09-01'
      AND facility_code IN (104, 141, 172, 49, 30, 16)
),
reference_weights AS (
    SELECT
        triage_category,
        1.0 * SUM(attendances)
        / NULLIF(
            SUM(SUM(attendances)) OVER (), 0
        ) AS triage_weight
    FROM triage_data
    GROUP BY triage_category
),
adjusted_performance AS (
    SELECT
        t.facility_code,
        t.facility_name,
        SUM(
            t.seen_within_target_pct * w.triage_weight
        ) AS adjusted_timeliness_pct,
        COUNT(t.seen_within_target_pct) AS valid_categories
    FROM triage_data t
    INNER JOIN reference_weights w
        ON t.triage_category = w.triage_category
    GROUP BY t.facility_code, t.facility_name
)
SELECT
    facility_name,
    ROUND(adjusted_timeliness_pct, 2)
        AS triage_adjusted_timeliness_pct,
    valid_categories
FROM adjusted_performance
ORDER BY triage_adjusted_timeliness_pct DESC;
