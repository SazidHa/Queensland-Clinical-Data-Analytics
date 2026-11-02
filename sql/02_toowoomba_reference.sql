
SELECT
    facility_code,
    facility_name,
    quarter_end_month,
    total_attendances,
    seen_within_target_pct,
    median_wait_minutes
FROM gold_ed_hospital_quarterly
WHERE facility_name LIKE '%Toowoomba%'
ORDER BY quarter_end_month DESC;
