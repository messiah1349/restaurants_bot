with pay_table as (
select
    case when user_id < payer then ps.payment_share else -ps.payment_share end as owe
    ,case when user_id < payer then user_id else payer end as user1
    ,case when user_id < payer then payer else user_id end as user2
from
    payment p
join
    payment_shares ps
    on
        p.payment_id = ps.payment_id
where
    p.is_resolve = 0
    and user_id <> payer
)
select
    pt.user1, pt.user2, u1.name, u2.name
    ,sum(owe) as owe
from
    pay_table pt
left join
    user u1
    on
        pt.user1 = u1.telegram_id
left join
    user u2
    on
        pt.user2 = u2.telegram_id
group by
    pt.user1, pt.user2, u1.name, u2.name
