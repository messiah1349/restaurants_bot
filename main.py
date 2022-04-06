from argparse import ArgumentParser

from lib.client import Client


def main():
    parser = ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--backend", choices=["testing", "prod"])

    args = parser.parse_args()

    client = Client(args.backend, args.token)
    client.run()


if __name__ == "__main__":
    main()
