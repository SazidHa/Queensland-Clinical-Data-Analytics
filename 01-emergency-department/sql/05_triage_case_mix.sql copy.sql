
SELECT
    facility_name,
    triage_category,
    SUM(attendances) AS triage_attendances,
    ROUND(
        100.0 * SUM(attendances)
        / NULLIF(
            SUM(SUM(attendances)) OVER (
                PARTITION BY facility_code
            ), 0
        ), 2
    ) AS triage_share_pct
FROM gold_ed_triage_performance
WHERE quarter_end_month = '2025-09-01'
  AND facility_code IN (
      104, 141, 172, 49, 30, 16
  )
GROUP BY
    facility_code,
    facility_name,
    triage_category
ORDER BY
    facility_name,
    triage_category;
