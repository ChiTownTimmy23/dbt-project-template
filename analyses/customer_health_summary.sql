select
    customer_status,
    count(*) as customer_count,
    sum(lifetime_value) as lifetime_value
from {{ ref('dim_customers') }}
group by customer_status
