import duckdb
import pandas as pd

result = duckdb.sql("""
    SELECT
        count(*) AS rows,
        count(*) - count(price) AS null_price,
        count(*) - count(DISTINCT order_id) AS dup_orders,
        count(DISTINCT category) AS category_values,
        min(order_date) AS first_date,
        max(order_date) AS last_date
    FROM 'orders_clean.parquet'
""").df()

print(result.to_string(index=False))

report = pd.read_csv('quality_report.csv').set_index('dataset')
after = report.loc['after']

matched = (
    result.loc[0, 'rows'] == after['rows']
    and result.loc[0, 'null_price'] == after['null_price']
    and result.loc[0, 'dup_orders'] == after['dup_order_id']
    and result.loc[0, 'category_values'] == after['category_values']
)

print('Pandas 보고서와 일치:', matched)

if not matched:
    raise SystemExit(1)
