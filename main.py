from gmanagr.auth import checkToken
from gmanagr.gmail_client import GmailClient
from gmanagr.app import Gmanagr


def main():
    creds = checkToken()
    GmailClient(creds)


if __name__ == "__main__":
    main()
    app = Gmanagr()
    app.run()
