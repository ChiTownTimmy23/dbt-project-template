select
    order_id,
    order_amount
from {{ ref('fct_orders') }}
where order_amount < 0
