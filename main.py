from auth import checkToken
from gmail_client import GmailClient


def main():
    creds = checkToken()
    GmailClient(creds)


if __name__ == "__main__":
    main()
