import os
import time
import sqlite3
import pandas as pd
from dataclasses import dataclass
from typing import List, Any, Dict, Tuple, Optional
import numpy as np

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))

import sys
sys.path.append(ROOT_DIR)
import lib.utils as ut


BD_NAME = f'{ROOT_DIR}/data/prod.db'

CONFIG_PATH = f'{ROOT_DIR}/tools/config.yaml'
config = ut.read_config(CONFIG_PATH)

PAYMENT_TYPES = config['payments_types']
RESTAURANT_MARK_DICT = config['restautant_mark']
SQL_QUERY_PATH = f'{ROOT_DIR}/tools/sql_queries/'
CALC_OWE_QUERY = 'calc_owe.sql'
GET_RESTAURANT_QUERY = 'get_restaurant.sql'
GET_RESTAURANT_MARK_QUERY = 'get_restaurant_mark.sql'


def _calc_times(time_str: str):

    if not time_str:
        time_unix = time.time()
        time_str = ut.unix_to_string(time_unix)
    else:
        time_unix = ut.string_to_unix(time_str)

    return time_unix, time_str


def _generate_table_insert_query(table_name: str, columns: List):
    query = f"""
    insert into {table_name}
    ({", ".join(columns)})
    values
    ({','.join(['?' for _ in range(len(columns))])});
    """
    return query

@dataclass
class Response:
    status: int
    answer: Any


class Backend:

    def __init__(self, db_name: Optional[str] = None):
        self.db_name = db_name

    def set_db(self, db_name: str):
        self.db_name = db_name

    def _get_db_connection(self):
        assert self.db_name is not None, "set db_name first"
        sqlite_connection = sqlite3.connect(self.db_name)
        return sqlite_connection

    def _execute_query(self, query: str, params=None):
        sqlite_connection = self._get_db_connection()
        cursor = sqlite_connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        sqlite_connection.commit()
        cursor.close()

    def _read_sql(self, query: str):
        sqlite_connection = self._get_db_connection()
        cursor = sqlite_connection.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        sqlite_connection.commit()
        cursor.close()

        return data

    def _generate_column_names(self, table_name: str) -> List:

        query = f"pragma table_info({table_name})"
        column_data = self._read_sql(query)
        column_data = sorted(column_data, key=lambda x: x[0])

        return [x[1] for x in column_data]

    def _get_table(self, table_name, condition) -> List:
        if condition:
            query = f"select * from {table_name} {condition}"
        else:
            query = f"select * from {table_name}"
        table = self._read_sql(query)
        return table

    def _get_table_info(self, table_name, clause=None):
        data = self._get_table(table_name, clause)
        columns = self._generate_column_names(table_name)
        table_info = [{column: value for column, value in zip(columns, row)} for row in data ]
        response = Response(1, table_info)
        return response

    def _insert_into_table(self, table_name: str, inserted_values: Tuple) -> None:
        columns = self._generate_column_names(table_name)
        query = _generate_table_insert_query(table_name, columns)
        self._execute_query(query, inserted_values)

    def _get_table_as_dataframe(self, table_name: str, condition=None) -> pd.DataFrame:
        data = self._get_table(table_name, condition)
        columns = self._generate_column_names(table_name)

        df = pd.DataFrame(data, columns=columns)
        return df

    def _insert_csv_to_table(self, table_name: str, path_to_file: str) -> None:
        df = pd.read_csv(path_to_file)
        inserted_values = df.apply(tuple, axis=1)
        for inserted_value in inserted_values:
            self._insert_into_table(table_name, inserted_value)

    def save_table_to_csv(self, table_name:str,  path_to_file: str):
        df = self._get_table_as_dataframe(table_name)
        df.to_csv(path_to_file, index=False)

    def replace_table_from_csv(self, table_name: str, path_to_file: str):
        delete_query = f"delete from {table_name}"
        self._execute_query(delete_query)
        self._insert_csv_to_table(table_name, path_to_file)

    def _check_user_exist(self, telegram_id: str, user_name: str) -> bool:
        users = self._get_table('user', None)
        if telegram_id in [x[0] for x in users] or user_name in [x[1] for x in users]:
            return True
        else:
            return False

    def _check_entity_by_id(self, entity, id_num, id_column, is_str):

        if is_str:
            query = f"""
                    select * from {entity}
                    where {id_column} = '{id_num}'
            """
        else:
            query = f"""
                    select * from {entity}
                    where {id_column} = {id_num}
            """
        query_answer = self._read_sql(query)
        return query_answer

    def _check_answer_not_uniqueness(self, entity, id_num, id_column, is_str=False):
        check_result = self._check_entity_by_id(entity, id_num, id_column, is_str)

        if not len(check_result):
            return Response(-1, f'there is no {entity} {id_num}')

        elif len(check_result) > 1:
            return Response(-1, f'there is more than 1 {entity} {id_num}')

        else:
            return None

    def _generate_id(self, table_name, id_column):
        query = f"select max({id_column}) from {table_name}"
        max_id = self._read_sql(query)[0][0]
        if not max_id:
            new_id = 1
        else:
            new_id = max_id + 1
        return new_id

    def _generate_payment_id(self):

        query = "select max(payment_id) from payment"
        max_id = self._read_sql(query)[0][0]
        if not max_id:
            new_id = 1
        else:
            new_id = max_id + 1
        return new_id

    def add_user(self, telegram_id: str, user_name: str) -> Response:

        if self._check_user_exist(telegram_id, user_name):
            return Response(-1, 'user has already existed')

        inserted_values = (telegram_id, user_name)
        self._insert_into_table('user', inserted_values)

        return Response(1, 'user_added')

    def get_users_list(self) -> Response:
        return self._get_table_info('user')

    def get_payment_list(self) -> Response:
        return self._get_table_info('payment', 'where is_deleted = 0')

    def get_unresolved_payment_list(self) -> Response:
        return self._get_table_info('payment', 'where is_resolve = 0 and is_deleted = 0')

    def get_restaurant_list(self) -> Response:
        return self._get_table_info('restaurant', 'where is_deleted = 0')

    def get_restaurant_mark_list(self) -> Response:

        query = ut.read_file(SQL_QUERY_PATH + GET_RESTAURANT_MARK_QUERY)
        data = self._read_sql(query)
        mark_dict_rev = {value: key for key, value in RESTAURANT_MARK_DICT.items()}
        data = [(val[0], val[1], mark_dict_rev[val[2]]) for val in data]
        columns = ['user_name', 'restaurant_name', 'mark']

        table_info = [{column: value for column, value in zip(columns, row)} for row in data]
        response = Response(1, table_info)
        return response

    def change_user_name(self, user_id, new_user_name) -> Response:

        user_id_not_uniqueness = self._check_answer_not_uniqueness('user', user_id, 'telegram_id')
        if user_id_not_uniqueness:
            return user_id_not_uniqueness

        user_name_checking = \
            self._check_entity_by_id('user', new_user_name, 'name', is_str=True)
        if len(user_name_checking):
            return Response(-1, f'user {new_user_name} have already existed')

        else:
            qu = f"""
                update user 
                set name = '{new_user_name}'
                where telegram_id = {user_id}
            """
            self._execute_query(qu)
            return Response(1, 'name was changed')

    def remove_user(self, user_id) -> Response:

        user_not_uniqueness = self._check_answer_not_uniqueness('user', user_id, 'telegram_id')
        if user_not_uniqueness: return user_not_uniqueness
        else:
            qu = f"""
                delete from user 
                where telegram_id = {user_id}
            """
            self._execute_query(qu)
            return Response(1, 'user was deleted')

    def _insert_shares(self, payment_id: int, shares: Dict) -> None:
        for user in shares:
            inserted_values = (payment_id, user, shares[user])
            self._insert_into_table('payment_shares', inserted_values)

    def _change_restaurant_is_new_flg(self, restaurant_id):

        query = f"""
            update restaurant
            set is_new = 0
            where 
                restaurant_id = {restaurant_id}
                and is_deleted = 0
                and is_new = 1
        """
        self._execute_query(query)


    def add_payment(self
                    ,total:float
                    ,payer:int
                    ,creator_id: int
                    ,shares:Dict
                    ,payment_type:str
                    ,payment_datetime:str=None
                    ,is_resolved=False
                    ,restaurant_id:int=None
                    ,comment:str=""
                    ) -> Response:

        # check_payer in bd
        user_not_uniqueness = self._check_answer_not_uniqueness('user', payer, 'telegram_id')
        if user_not_uniqueness:
            return user_not_uniqueness

        # check all shares in bd
        for user_id in shares:
            user_not_uniqueness = self._check_answer_not_uniqueness('user', user_id, 'telegram_id')
            if user_not_uniqueness: return user_not_uniqueness

        # check payment type valid
        if payment_type not in PAYMENT_TYPES:
            return Response(-1, 'not valid payment_type')

        # check restaurant in db
        if restaurant_id:
            restaurant_not_uniqueness = \
                self._check_answer_not_uniqueness('restaurant', restaurant_id, 'restaurant_id')
            if restaurant_not_uniqueness:
                return restaurant_not_uniqueness

            self._change_restaurant_is_new_flg(restaurant_id)

        # insert values to restaurant table
        payment_id = self._generate_payment_id()
        datetime_unix, datetime_str = _calc_times(payment_datetime)
        inserted_values = (payment_id, total, payer, creator_id, datetime_unix, datetime_str, payment_type,
                         restaurant_id, int(is_resolved),comment, 0)

        self._insert_into_table('payment', inserted_values)

        #insert payment shares to table
        self._insert_shares(payment_id, shares)

        return Response(1, 'Payment was added')

    def resolve(self, creator_id: int) -> Response:

        user_not_uniqueness = self._check_answer_not_uniqueness('user', creator_id, 'telegram_id')
        if user_not_uniqueness: return user_not_uniqueness

        query = """
            update payment
            set is_resolve = 1
            where is_resolve = 0 
        """
        self._execute_query(query)
        inserted_params = (creator_id, time.time())
        self._insert_into_table('resolve_history', inserted_params)

        return Response(1, 'all payments were resolved')

    def get_owes(self):
        query = ut.read_file(SQL_QUERY_PATH + CALC_OWE_QUERY)
        query_answer = self._read_sql(query)

        owes = []

        for row in query_answer:
            user1_id, user2_id, user1_name, user2_name, owe = row
            if owe > 0:
                curr_resp = {
                    'id_from': user1_id,
                    'id_to': user2_id,
                    'user_from': user1_name,
                    'user_to': user2_name,
                    'owe': owe}
            else:
                curr_resp = {
                    'id_from': user2_id,
                    'id_to': user1_id,
                    'user_from': user2_name,
                    'user_to': user1_name,
                    'owe': -owe}
            owes.append(curr_resp)

        return Response(1, owes)

    def add_restaurant(self, \
            restaurant_name: str, is_fast: bool=False, is_near: bool=False, is_new: bool=True):

        exist_check_result = self._check_entity_by_id('restaurant', restaurant_name, 'name', is_str=True)
        if len(exist_check_result):
            return Response(-1, f'restaurant {restaurant_name} is already existed')

        restaurant_id = self._generate_id('restaurant', 'restaurant_id')

        inserted_values = (restaurant_id, restaurant_name, int(is_fast), int(is_near), int(is_new), 0)
        self._insert_into_table('restaurant', inserted_values)

        return Response(1, 'restaurant was added')


    def _remove_entity(self, table_name, entity, column_name, deleted_column = 'is_deleted', is_str=False) -> Response:

        entity_not_uniqueness = self._check_answer_not_uniqueness(table_name, entity, column_name, is_str)
        if entity_not_uniqueness: return entity_not_uniqueness

        delete_query = f"update {table_name} set {deleted_column} = 1 where {column_name} = {entity}"
        self._execute_query(delete_query)

        return Response(1, f'{table_name} was deleted')


    def remove_restaurant(self, restaurant_id: int) -> Response:
        return self._remove_entity('restaurant', restaurant_id, 'restaurant_id')

    def delete_payment(self, payment_id) -> Response:
        return self._remove_entity('payment', payment_id, 'payment_id')

    def _update_rest_mark_actuality(self, restaurant_id, user_id):

        change_actual_query = f"""
                    update restaurant_mark 
                    set is_actual = 0
                    where 1=1
                        and is_actual = 1
                        and restaurant_id = {restaurant_id}
                        and user_id = {user_id}
                """
        self._execute_query(change_actual_query)

    def add_restaurant_mark(self, restaurant_id, user_id, mark):

        user_not_uniqueness = self._check_answer_not_uniqueness('user', user_id, 'telegram_id')
        if user_not_uniqueness: return user_not_uniqueness

        restaraunt_not_uniqueness = self._check_answer_not_uniqueness('restaurant', restaurant_id, 'restaurant_id')
        if restaraunt_not_uniqueness: return restaraunt_not_uniqueness

        # check mark value
        if mark not in RESTAURANT_MARK_DICT:
            return Response(-1, 'mark is not from mark allowed list')

        self._update_rest_mark_actuality(restaurant_id, user_id)

        current_time = time.time()

        value_mark = RESTAURANT_MARK_DICT[mark]

        inserted_values = (restaurant_id, user_id, value_mark, current_time, 1)
        self._insert_into_table('restaurant_mark', inserted_values)

        return Response(1, 'mark was added')

    def get_random_restaurant(self, is_fast: bool = None, is_near: bool = None, is_new: bool = None):
        query = ut.read_file(SQL_QUERY_PATH + GET_RESTAURANT_QUERY)

        condition = ''

        if is_fast is not None:
            condition += f'and r.is_fast = {int(is_fast)}\n'

        if is_near is not None:
            condition += f'and r.is_near = {int(is_near)}\n'

        if is_new is not None:
            condition += f'and r.is_new = {int(is_new)}\n'

        rest_data = self._read_sql(query.format(condition=condition))
        rest_size = len(rest_data)

        if not rest_size:
            return Response(1, [])

        preds = np.array([x[2] for x in rest_data])
        preds_norm = preds / preds.sum()

        choice = np.random.choice(range(rest_size), size=rest_size, replace=False, p=preds_norm)

        rest_data_choiced = [rest_data[ix] for ix in choice]

        ret = [{'restaurant_id': rest[0], 'restaurant_name': rest[1]} for rest in rest_data_choiced]

        return Response(1, ret)


if __name__ == '__main__':
    pass
