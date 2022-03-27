select
    u.name as user_name
    ,r.name as restaurant_name
    ,rm.mark
from
    restaurant_mark rm
join
    user u
    on
        rm.user_id = u.telegram_id
join
    restaurant r
    on
        rm.restaurant_id = r.restaurant_id
where
    r.is_deleted = 0
    and rm.is_actual = 1
;