import sqlite3
from dataclasses import dataclass
from typing import List, Any, Dict
import subprocess
import time

import utils as ut

BD_NAME = 'sqlite_python.db'
PAYMENT_TYPES = ('restaurant', 'other')


def _generate_user_insert_query(telegram_id: str, user_name: str):
    query = f"""
        insert into user
        (telegram_id, name) values ('{telegram_id}', '{user_name}')
    """
    return query


def _generate_payment_shares_insert_query(payment_id: int, user_id: int, payment_share: float):
    query = f"""
        insert into payment_shares
        (payment_id, user_id, payment_share) values
        ({payment_id}, {user_id}, {payment_share})
    """

    return query


def _calc_times(time_str:str):

    if not time_str:
        time_unix = time.time()
        time_str = ut.unix_to_string(time_unix)
    else:
        time_unix = ut.string_to_unix(time_str)

    return time_unix, time_str

def _generate_payment_insert_query():
    query = """
    insert into payment
    (payment_id, total_sum, payer, creator_id, datetime_unix, datetime_str, payment_type, restaurant_id,
     is_resolve, comment)
    values
    (?,?,?,?,?,?,?,?,?,?);
    """

    return query


@dataclass
class Response:
    status: int
    answer: Any


class BackEnd:

    def __init__(self, bd_name: str):
        self.bd_name = bd_name

    def _get_bd_connection(self):
        sqlite_connection = sqlite3.connect(self.bd_name)
        return sqlite_connection

    def _execute_query(self, query: str, params=None):
        sqlite_connection = self._get_bd_connection()
        cursor = sqlite_connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        sqlite_connection.commit()
        cursor.close()

    def _read_sql(self, query: str):
        sqlite_connection = self._get_bd_connection()
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

    def _get_table(self, table_name, clause) -> List:
        if clause:
            query = f"select * from {table_name} {clause}"
        else:
            query = f"select * from {table_name}"
        table = self._read_sql(query)
        return table

    def _check_user_exist(self, telegram_id: str, user_name: str) -> bool:
        users = self._get_table('user', None)
        if telegram_id in [x[0] for x in users] or user_name in [x[1] for x in users]:
            return True
        else:
            return False

    def _check_entity_by_id(self, entity, id_num, id_column):

        query = f"""
                select * from {entity}
                where {id_column} = {id_num}
        """

        query_answer = self._read_sql(query)
        return query_answer

    def _check_answer_not_uniqueness(self, entity, id_num, id_column):
        check_result = self._check_entity_by_id(entity, id_num, id_column)

        if len(check_result) == 0:
            return Response(-1, f'there is no {entity} {id_num}')

        elif len(check_result) > 1:
            return Response(-1, f'there is more than 1 {entity} {id_num}')

        else:
            return None

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

        query = _generate_user_insert_query(telegram_id, user_name)
        self._execute_query(query)
        response = Response(1, 'user_added')

        return response

    def _get_table_info(self, table_name, clause=None):
        data = self._get_table(table_name, clause)
        columns = self._generate_column_names(table_name)
        table_info = [{column: value for column, value in zip(columns, row)} for row in data ]
        response = Response(1, table_info)
        return response

    def get_users_list(self):
        return self._get_table_info('user')

    def get_payment_list(self):
        return self._get_table_info('payment')

    def get_unresolved_payment_list(self):
        return self._get_table_info('payment', 'where is_resolve = 0')

    def change_user_name(self, user_id, new_user_name):

        user_not_uniqueness = self._check_answer_not_uniqueness('user', user_id, 'telegram_id')
        if user_not_uniqueness: return user_not_uniqueness

        else:

            qu = f"""
                update user 
                set name = '{new_user_name}'
                where telegram_id = {user_id}
            """
            self._execute_query(qu)
            return Response(1, 'name was changed')

    def remove_user(self, user_id):

        user_not_uniqueness = self._check_answer_not_uniqueness('user', user_id, 'telegram_id')
        if user_not_uniqueness:
            return user_not_uniqueness

        else:
            qu = f"""
                delete from user 
                where telegram_id = {user_id}
            """
            self._execute_query(qu)
            return Response(1, 'user was deleted')

    def _insert_shares(self, payment_id: int, shares: Dict) -> None:
        for user in shares:
            insert_params = (payment_id, user, shares[user])
            qu = _generate_payment_shares_insert_query(*insert_params)
            self._execute_query(qu)

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
                    ):

        # check_payer in bd
        user_not_uniqueness = self._check_answer_not_uniqueness('user', payer, 'telegram_id')
        if user_not_uniqueness: return user_not_uniqueness

        # check all shares in bd
        for user_id in shares:
            user_not_uniqueness = self._check_answer_not_uniqueness('user', user_id, 'telegram_id')
            if user_not_uniqueness: return user_not_uniqueness

        # check payment type valid
        if payment_type not in PAYMENT_TYPES:
            return Response(-1, 'not valid payment_type')

        # check restaurant in bd to be done

        payment_id = self._generate_payment_id()

        datetime_unix, datetime_str = _calc_times(payment_datetime)

        insert_params = (payment_id, total, payer, creator_id, datetime_unix, datetime_str, payment_type,
                         restaurant_id, int(is_resolved),comment)

        insert_query = _generate_payment_insert_query()
        self._execute_query(insert_query, insert_params)

        #insert payment shares to table
        self._insert_shares(payment_id, shares)

        return Response(1, 'Payment was added')

    def delete_payment(self, payment_id):

        payment_not_uniqueness = self._check_answer_not_uniqueness('payment', payment_id, 'payment_id')
        if payment_not_uniqueness: return payment_not_uniqueness

        delete_query = f"delete from payment where payment_id = {payment_id}"
        self._execute_query(delete_query)

        return Response(1, 'payment was deleted')


    def _test(self):
        qu = "select max(payment_id) from payment"
        data = self._read_sql(qu)
        print(data)


if __name__ == '__main__':
    pass