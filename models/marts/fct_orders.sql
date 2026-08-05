select
    order_id,
    customer_id,
    order_date,
    order_status,
    cast(amount_cents / 100.0 as decimal(18, 2)) as order_amount
from {{ ref('stg_orders') }}
