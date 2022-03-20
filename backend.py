import sqlite3
from dataclasses import dataclass
from typing import List, Any, Dict
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

    def _get_users(self) -> List:
        query = "select * from user"
        user_table = self._read_sql(query)
        return user_table

    def _check_user_exist(self, telegram_id: str, user_name: str) -> bool:
        users = self._get_users()
        if telegram_id in [x[0] for x in users] or user_name in [x[1] for x in users]:
            return True
        else:
            return False

    def _check_user_by_id(self, user_id):
        check_user_qu = f"""
                select * from user
                where telegram_id = {user_id}
                """

        check_users_result = self._read_sql(check_user_qu)

        return check_users_result

    def _check_answer_not_uniqueness(self, user_id):
        check_users_result = self._check_user_by_id(user_id)

        if len(check_users_result) == 0:
            return Response(-1, f'there is no user {user_id}')

        elif len(check_users_result) > 1:
            return Response(-1, f'there is more than 1 user {user_id}')

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

    def get_users_list(self):
        users = self._get_users()
        user_names = [x[1] for x in users]
        response = Response(1, user_names)
        return response

    def change_user_name(self, user_id, new_user_name):

        user_not_uniqueness = self._check_answer_not_uniqueness(user_id)
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

        user_not_uniqueness = self._check_answer_not_uniqueness(user_id)
        if user_not_uniqueness:
            return user_not_uniqueness

        else:
            qu = f"""
                delete from user 
                where telegram_id = {user_id}
            """
            self._execute_query(qu)
            return Response(1, 'user was deleted')

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
        user_not_uniqueness = self._check_answer_not_uniqueness(payer)
        if user_not_uniqueness: return user_not_uniqueness

        # check all shares in bd
        for user_id in shares:
            user_not_uniqueness = self._check_answer_not_uniqueness(user_id)
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

        return Response(1, 'Payment was added')

    def _get_unresolved_payment(self):
        qu = "select * from payment where is_resolve = 0"
        data = self._read_sql(qu)
        return data


    def _test(self):
        qu = "select max(payment_id) from payment"
        data = self._read_sql(qu)
        print(data)


if __name__ == '__main__':
    pass