select
    customer_id,
    customer_name,
    signup_date,
    customer_status,
    order_count,
    completed_order_count,
    cast(lifetime_value_cents / 100.0 as decimal(18, 2)) as lifetime_value,
    first_order_date,
    last_order_date
from {{ ref('int_customer_order_metrics') }}
