import sqlite3

import utils as ut

BD_NAME = 'sqlite_python.db'
SQL_QUERY_PATH = 'sql_queries/'
USER_CREATE_QUERY = 'create_user_table.sql'


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


def create_user_table():
    query = ut.read_file(SQL_QUERY_PATH + USER_CREATE_QUERY)

    sqlite_connection = sqlite3.connect(BD_NAME)

    cursor = sqlite_connection.cursor()
    cursor.executescript(query)
    sqlite_connection.commit()
    print("user table created")
    cursor.close()


if __name__ == '__main__':
    create_bd()
    create_user_table()

