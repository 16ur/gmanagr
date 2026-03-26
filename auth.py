from google_auth_oauthlib.flow import InstalledAppFlow


async def defineScope():
    return InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.settings.basic",
        ],
    )


async def openLocalServer(flow):
    flow.run_local_server()
    return flow.authorized_session()


profile_info = session.get("https://www.googleapis.com/userinfo/v2/me").json()


print(profile_info)
