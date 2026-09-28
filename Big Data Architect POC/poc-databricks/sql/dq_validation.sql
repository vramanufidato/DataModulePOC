-- DQ validation between Silver and Gold
-- Fails the task if any check returns non-zero

WITH checks AS (
  SELECT
    COUNTIF(order_id IS NULL)              AS null_ids,
    COUNT(*) - COUNT(DISTINCT order_id)    AS dup_ids,
    COUNTIF(amount <= 0)                   AS bad_amounts,
    COUNTIF(order_date IS NULL)            AS null_dates
  FROM ${catalog}.silver.clean_orders
  WHERE DATE(ingested_at) = CURRENT_DATE()
)
SELECT
  CASE
    WHEN null_ids    > 0 THEN RAISE_ERROR(CONCAT('Null order_ids: ',    null_ids))
    WHEN dup_ids     > 0 THEN RAISE_ERROR(CONCAT('Duplicate order_ids: ', dup_ids))
    WHEN bad_amounts > 0 THEN RAISE_ERROR(CONCAT('Non-positive amounts: ', bad_amounts))
    WHEN null_dates  > 0 THEN RAISE_ERROR(CONCAT('Null order_dates: ',  null_dates))
    ELSE 'PASS'
  END AS dq_result
FROM checks;
