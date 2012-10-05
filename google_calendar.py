from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow, AccessTokenRefreshError
from oauth2client.tools import run
import httplib2
import rfc3339

class CalendarApi(object):
    def __init__(self, service):
        self.service = service

    @classmethod
    def authorize(cls):
        client_id = '931825167006.apps.googleusercontent.com'
        client_secret = 'mJ_MYwwdDcPDRbXEmiMp3scS'
        scope = 'https://www.googleapis.com/auth/calendar'

        flow = OAuth2WebServerFlow(client_id, client_secret, scope)
        storage = Storage('credentials.dat')
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            credentials = run(flow, storage)
        http = credentials.authorize(httplib2.Http())
        return cls(build('calendar', 'v3', http=http))

    def create_event(self, start, end):
        event = {
            'summary': 'Consultant shift',
            'location': 'Trottier 3rd',
            'start': {
                'timeZone': 'America/Montreal',
                'dateTime': rfc3339.rfc3339(start),
            },
            'end': {
                'timeZone': 'America/Montreal',
                'dateTime': rfc3339.rfc3339(end),
            },
        }
        try:
            events = self.service.events()
            return events.insert(calendarId='primary', body=event).execute()
        except AccessTokenRefreshError:
            print 'Your Google credentials have expired (or been revoked).'
            print 'Re-run the script to reauthorize.'
