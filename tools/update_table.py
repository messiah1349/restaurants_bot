import argparse
from lib.backend import Backend


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("database")
    parser.add_argument("table_name")
    parser.add_argument("csv_table")

    args = parser.parse_args()

    backend = Backend(args.db)
    backend.replace_table_from_csv(args.table_name, args.csv_table)


if __name__ == "__main__":
    main()
