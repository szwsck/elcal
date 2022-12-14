import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/spreadsheets']
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if creds.expired:
        creds.refresh(Request())
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
else:
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

gcal = build('calendar', 'v3', credentials=creds)
sheets = build('sheets', 'v4', credentials=creds).spreadsheets()
