import imaplib
import email
from email import utils as email_utils
from datetime import date, timedelta, datetime, time
import base64
import re
import calendar
import collections
import argparse

from google_calendar import CalendarApi

def last_monday():
    today = date.today()
    monday = today - timedelta(days=today.weekday(), weeks=1)
    return monday.strftime('%d-%b-%Y')

_months = '|'.join(calendar.month_abbr[month] for month in range(1, 13))
_pattern = re.compile(r'for\s+(%s) (\d+)' % _months) 
def get_monday_date(header):
    match = ' '.join(_pattern.findall(header)[0])
    year = date.today().year
    return datetime.strptime(match, '%b %d').replace(year=year).date()

class Mailbox(object):
    def __init__(self, host, port, username, password):
        self.M = imaplib.IMAP4_SSL(host, port)
        self.M.login(username, password)
        self.M.select()

    def _build_schedule(self, s):
        def _clean(s):
            return s.strip(' \r\t')
        s = s.replace('\r\t', '\n')
        lines = [_clean(l) for l in s.split('\n') if _clean(l)]
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                'Saturday', 'Sunday']
        week_date = get_monday_date(lines[0])
        schedule_by_day = []
        for i, day in enumerate(days):
            index = lines.index(day)
            next_index = None
            if i < len(days) - 1:
                next_index = lines.index(days[i + 1])
            schedule_by_day.append(lines[index + 1:next_index])
        schedule_by_name = collections.defaultdict(list)
        for i, shifts in enumerate(schedule_by_day):
            for shift in shifts:
                shift, name = shift.split()
                shift = time(hour=int(shift.split('-')[0]))
                s = datetime.combine(week_date + timedelta(days=i), shift)
                schedule_by_name[name].append((s, s + timedelta(hours=2)))
        for name, schedule in schedule_by_name.items():
            i = 1
            while i < len(schedule):
                if schedule[i - 1][1].hour == schedule[i][0].hour:
                    combined = (schedule[i - 1][0], schedule[i][1])
                    schedule.insert(i - 1, combined)
                    del schedule[i]
                    del schedule[i]
                else:
                    i += 1
        return schedule_by_name

    def _extract_schedule(self, raw_email):
        message = email.message_from_string(raw_email)
        raw_attachment = message.get_payload(1).get_payload()
        schedule = base64.b64decode(raw_attachment)
        return self._build_schedule(schedule)

    def schedules(self):
        criteria = ['(FROM "Faiyaz")',
                    '(SUBJECT "Schedule for")',
                    '(NOT SUBJECT "Re:")',
                    '(NOT SUBJECT "Fwd:")',
                    '(SENTSINCE "%s")' % last_monday()]
        for num in self.M.search(None, *criteria)[1][0].split():
            raw_email = self.M.fetch(num, '(RFC822)')[1][0][1]
            yield self._extract_schedule(raw_email)

def parse_args():
    parser = argparse.ArgumentParser(
        description='manage SOCS consultant schedule',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--host',
        default='exchange.mcgill.ca', metavar='host',
        help='IMAP host to fetch from')
    parser.add_argument('--port',
        default=993, type=int, metavar='port',
        help='IMAP port')
    parser.add_argument('--username',
        required=True, metavar='user',
        help='IMAP username')
    parser.add_argument('--password',
        required=True, metavar='pass',
        help='IMAP password')
    parser.add_argument('--name',
        required=True, metavar='name',
        help='Your first name (as it appears on the consultant schedule))')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    mailbox = Mailbox(host=args.host, port=args.port,
                      username=args.username, password=args.password)
    schedule = next(mailbox.schedules())
    calendar = CalendarApi.authorize()
    for shift in schedule[args.name]:
        calendar.create_event(shift[0], shift[1])
