import sqlite3

import utils as ut

BD_NAME = 'sqlite_python.db'
SQL_QUERY_PATH = 'sql_queries/'
USER_CREATE_QUERY = 'create_user_table.sql'
PAYMENT_CREATE_QUERY = 'create_payment_table.sql'
PAYMENT_SHARES_CREATE_QUERY = 'create_payment_shares_table.sql'


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


def create_user_table():

    path = SQL_QUERY_PATH + USER_CREATE_QUERY
    create_table_from_script(path)
    print("user table created")


def create_payment_table():

    path = SQL_QUERY_PATH + PAYMENT_CREATE_QUERY
    create_table_from_script(path)
    print("payment table created")


def create_payment_share_table():

    path = SQL_QUERY_PATH + PAYMENT_SHARES_CREATE_QUERY
    create_table_from_script(path)
    print("payment_shares table created")


if __name__ == '__main__':
    # create_bd()
    # create_user_table()
    create_payment_table()
    # create_payment_share_table()


