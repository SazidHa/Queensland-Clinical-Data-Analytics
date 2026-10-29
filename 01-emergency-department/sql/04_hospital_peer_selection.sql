
SELECT
    facility_code,
    facility_name,
    total_attendances,
    seen_within_target_pct,
    median_wait_minutes,
    ed_stay_within_4h_pct
FROM gold_ed_hospital_quarterly
WHERE quarter_end_month = '2025-09-01'
  AND total_attendances BETWEEN 12032 AND 20054
ORDER BY total_attendances DESC;
