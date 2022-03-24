import sqlite3
import sys
sys.path.append('../lib/')

import utils as ut

BD_NAME = '../data/prod.db'
SQL_QUERY_PATH = 'sql_queries/'
USER_CREATE_QUERY = 'create_user_table.sql'
PAYMENT_CREATE_QUERY = 'create_payment_table.sql'
PAYMENT_SHARES_CREATE_QUERY = 'create_payment_shares_table.sql'
RESOLVE_HISTORY_CREATE_QUERY = 'create_resolve_history.sql'
RESTAURANT_CREATE_QUERY = 'create_restaurant_table.sql'
RESTAURANT_MARK_CREATE_QUERY = 'create_restaurant_mark_table.sql'


def create_bd():
    try:
        sqlite_connection = sqlite3.connect(BD_NAME)
        cursor = sqlite_connection.cursor()
        print(f"sql bd {BD_NAME}  is created")

        sqlite_select_query = "select sqlite_version();"
        cursor.execute(sqlite_select_query)
        record = cursor.fetchall()
        print("version of bd SQLite: ", record)
        cursor.close()
    except sqlite3.Error as error:
        print("connection error", error)
    finally:
        if (sqlite_connection):
            sqlite_connection.close()
            print("connection closed")


def create_table_from_script(script_path:str) -> None:
    query = ut.read_file(script_path)

    sqlite_connection = sqlite3.connect(BD_NAME)
    cursor = sqlite_connection.cursor()
    cursor.executescript(query)
    sqlite_connection.commit()
    cursor.close()

def create_table(table_name: str, query_file: str) -> None:
    path = SQL_QUERY_PATH + query_file
    create_table_from_script(path)
    print(f"{table_name} table created")


if __name__ == '__main__':
    # create_bd()
    # create_user_table()
    # create_payment_table()
    # create_payment_share_table()
    # create_resolve_history_table()
    # create_table('restaurant', RESTAURANT_CREATE_QUERY)
    create_table('restaurant_mark', RESTAURANT_MARK_CREATE_QUERY)


