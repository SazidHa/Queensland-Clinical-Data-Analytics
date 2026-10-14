
WITH Toowoomba AS (
    SELECT
        total_attendances AS reference_attendances
    FROM gold_ed_hospital_quarterly
    WHERE facility_code = 104
      AND quarter_end_month = '2025-09-01'
)

SELECT
    h.facility_code,
    h.facility_name,
    h.total_attendances,
    h.seen_within_target_pct,
    h.median_wait_minutes,
    h.ed_stay_within_4h_pct,

    ROUND(
        100.0 *
        (h.total_attendances - t.reference_attendances)
        / NULLIF(t.reference_attendances, 0),
        2
    ) AS volume_difference_pct

FROM gold_ed_hospital_quarterly h
CROSS JOIN Toowoomba t

WHERE h.quarter_end_month = '2025-09-01'
  AND h.total_attendances BETWEEN
      t.reference_attendances * 0.75
      AND t.reference_attendances * 1.25

ORDER BY h.total_attendances DESC;
