import duckdb

duckdb.sql("""
    SELECT
        count(*) AS rows,
        count(*) - count(price) AS null_price,
        count(*) - count(DISTINCT order_id) AS dup_orders,
        count(DISTINCT category) AS category_values
    FROM 'orders.csv'
""").show()

duckdb.sql("""
    SELECT
        '[' || category || ']' AS category_visible,
        count(*) AS cnt
    FROM 'orders.csv'
    GROUP BY category
    ORDER BY cnt DESC, category
""").show()
