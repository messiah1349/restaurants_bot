select
    r.restaurant_id
    ,r.name
    ,avg(ifnull(rm.mark, 0.5)) as avg_mark
from
    restaurant r
cross join
    user u
left join
    restaurant_mark rm
    on
        r.restaurant_id = rm.restaurant_id
        and u.telegram_id = rm.user_id
where 1=1
    and r.is_deleted = 0
    and ifnull(rm.is_actual, 1) = 1
    {condition}
group by
    r.restaurant_id
    ,r.name
having
    min(mark) > 0
;