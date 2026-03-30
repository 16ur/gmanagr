from gmanagr.auth import checkToken
from gmanagr.gmail_client import GmailClient


def main():
    creds = checkToken()
    GmailClient(creds)


if __name__ == "__main__":
    main()
