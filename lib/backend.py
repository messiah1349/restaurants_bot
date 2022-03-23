import time
import sqlite3
from dataclasses import dataclass
from typing import List, Any, Dict, Tuple, Optional

import lib.utils as ut

PAYMENT_TYPES = ('restaurant', 'other')
SQL_QUERY_PATH = 'tools/sql_queries/'
CALC_OWE_QUERY = 'calc_owe.sql'


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

        inserted_values = (telegram_id, user_name)
        self._insert_into_table('user', inserted_values)

        return Response(1, 'user_added')

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

    def get_users_list(self) -> Response:
        return self._get_table_info('user')

    def get_payment_list(self) -> Response:
        return self._get_table_info('payment')

    def get_unresolved_payment_list(self) -> Response:
        return self._get_table_info('payment', 'where is_resolve = 0')

    def change_user_name(self, user_id, new_user_name) -> Response:

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
        inserted_values = (payment_id, total, payer, creator_id, datetime_unix, datetime_str, payment_type,
                         restaurant_id, int(is_resolved),comment)

        self._insert_into_table('payment', inserted_values)

        #insert payment shares to table
        self._insert_shares(payment_id, shares)

        return Response(1, 'Payment was added')

    def delete_payment(self, payment_id) -> Response:

        payment_not_uniqueness = self._check_answer_not_uniqueness('payment', payment_id, 'payment_id')
        if payment_not_uniqueness: return payment_not_uniqueness

        delete_query = f"delete from payment where payment_id = {payment_id}"
        self._execute_query(delete_query)

        return Response(1, 'payment was deleted')

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


if __name__ == '__main__':
    pass
