create table payment (
payment_id int not null
,total_sum real not null
,payer int not null
,creator_id int
,datetime_unix int
,datetime_str text
,payment_type text
,restaurant_id int
,is_resolve int not null
,comment text
,is_deleted int not null
);