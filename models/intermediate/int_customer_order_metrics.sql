with customers as (
    select *
    from {{ ref('stg_customers') }}
),

orders as (
    select *
    from {{ ref('stg_orders') }}
),

order_metrics as (
    select
        customer_id,
        cast(count(order_id) as bigint) as order_count,
        cast(
            sum(case when order_status = 'completed' then 1 else 0 end)
            as bigint
        ) as completed_order_count,
        cast(
            sum(case when order_status = 'completed' then amount_cents else 0 end)
            as bigint
        ) as lifetime_value_cents,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date
    from orders
    group by customer_id
),

final as (
    select
        customers.customer_id,
        customers.customer_name,
        customers.signup_date,
        customers.customer_status,
        cast(coalesce(order_metrics.order_count, 0) as bigint) as order_count,
        cast(coalesce(order_metrics.completed_order_count, 0) as bigint)
            as completed_order_count,
        cast(coalesce(order_metrics.lifetime_value_cents, 0) as bigint)
            as lifetime_value_cents,
        order_metrics.first_order_date,
        order_metrics.last_order_date
    from customers
    left join order_metrics
        on customers.customer_id = order_metrics.customer_id
)

select *
from final
