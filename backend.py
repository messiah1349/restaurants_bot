import sqlite3
from dataclasses import dataclass
from typing import List

BD_NAME = 'sqlite_python.db'


def _generate_user_insert_query(telegram_id: str, user_name: str):
    query = f"""
        insert into user
        (telegram_id, name) values ('{telegram_id}', '{user_name}')
    """
    return query


@dataclass
class Response:
    status: int
    answer: str


class BackEnd:

    def __init__(self, bd_name: str):
        self.bd_name = bd_name

    def _get_bd_connection(self):
        sqlite_connection = sqlite3.connect(self.bd_name)
        return sqlite_connection

    def _execute_query(self, query: str):
        sqlite_connection = self._get_bd_connection()
        cursor = sqlite_connection.cursor()
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
        return user_names

    def change_user_name(self, user_id, new_user_name):

        qu = f"""
            update user 
            set name = '{new_user_name}'
            where telegram_id = {user_id}
        """

        self._execute_query(qu)

    def remove_user(self, user_id):

        qu = f"""
            delete from user 
            where telegram_id = {user_id}
        """

        self._execute_query(qu)


if __name__ == '__main__':
    backend = BackEnd(BD_NAME)
    resp = backend.add_user(1488, 'putin')

    print(resp)
    backend.remove_user(1488)
    users = backend._get_users()
    print(users)
    user_list = backend.get_users_list()
    print(user_list)