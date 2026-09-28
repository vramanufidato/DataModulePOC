CREATE OR REPLACE TABLE ${catalog}.gold.daily_revenue
PARTITION BY order_date
CLUSTER BY region, category AS
SELECT
  DATE(o.order_ts) AS order_date,
  c.region,
  p.category,
  SUM(o.amount) AS revenue,
  COUNT(DISTINCT o.order_id) AS orders
FROM ${catalog}.silver.clean_orders o
JOIN ${catalog}.silver.clean_customers c USING (customer_id)
JOIN ${catalog}.silver.clean_products p USING (product_id)
WHERE DATE(o.order_ts) = CURRENT_DATE()
GROUP BY 1, 2, 3;
