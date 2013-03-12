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

    def get_available_colors(self):
        response = self.service.colors().get().execute()
        return response['event'].keys()

    def create_event(self, name, color, start, end):
        event = {
            'summary': name,
            'colorId': color,
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
            calendarId = '22f209nv6do0e2c5e4v0l9tl04@group.calendar.google.com'
            return events.insert(calendarId=calendarId, body=event).execute()
        except AccessTokenRefreshError:
            print 'Your Google credentials have expired (or been revoked).'
            print 'Re-run the script to reauthorize.'
