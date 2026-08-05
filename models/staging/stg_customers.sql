with source as (
    select *
    from {{ source('raw', 'raw_customers') }}
),

renamed as (
    select
        cast(customer_id as integer) as customer_id,
        cast(customer_name as varchar) as customer_name,
        cast(signup_date as date) as signup_date,
        cast(status as varchar) as customer_status
    from source
)

select *
from renamed
