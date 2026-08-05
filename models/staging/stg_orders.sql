with source as (
    select *
    from {{ source('raw', 'raw_orders') }}
),

renamed as (
    select
        cast(order_id as integer) as order_id,
        cast(customer_id as integer) as customer_id,
        cast(order_date as date) as order_date,
        cast(status as varchar) as order_status,
        cast(amount_cents as bigint) as amount_cents
    from source
)

select *
from renamed
