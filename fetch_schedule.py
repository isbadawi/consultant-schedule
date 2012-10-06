import imaplib
import email
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
    "Extract the start date from 'Schedule for  <m d> - <m d> <year>'"
    match = ' '.join(_pattern.findall(header)[0])
    year = date.today().year
    return datetime.strptime(match, '%b %d').replace(year=year).date()

def fetch_latest_schedule(host, port, username, password):
    M = imaplib.IMAP4_SSL(host, port)
    M.login(username, password)
    M.select()
    criteria = ['(FROM "Faiyaz")',
                '(SUBJECT "Schedule for")',
                '(NOT SUBJECT "Re:")',
                '(NOT SUBJECT "Fwd:")',
                '(SENTSINCE "%s")' % last_monday()]
    num = M.search(None, *criteria)[1][0].split()[0]
    raw_email = M.fetch(num, '(RFC822)')[1][0][1]
    message = email.message_from_string(raw_email)
    raw_attachment = message.get_payload(1).get_payload()
    return base64.b64decode(raw_attachment)

def build_schedule(s):
    def _clean(s):
        return s.strip(' \r\t')
    s = s.replace('\r\t', '\n')
    lines = [_clean(l) for l in s.split('\n') if _clean(l)]
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
            'Saturday', 'Sunday']
    week_date = get_monday_date(lines[0])
    # schedule_by_day maps days (Monday is 0) to lists of lines like
    # '<start>-<end> <name>'
    schedule_by_day = []
    for i, day in enumerate(days):
        index = lines.index(day)
        next_index = None
        if i < len(days) - 1:
            next_index = lines.index(days[i + 1])
        schedule_by_day.append(lines[index + 1:next_index])
    # schedule_by_name maps consultant names to lists of
    # (start, end) tuples, where start and end are datetimes
    schedule_by_name = collections.defaultdict(list)
    for i, shifts in enumerate(schedule_by_day):
        for shift in shifts:
            shift, name = shift.split()
            shift = time(hour=int(shift.split('-')[0]))
            s = datetime.combine(week_date + timedelta(days=i), shift)
            schedule_by_name[name].append((s, s + timedelta(hours=2)))
    for schedule in schedule_by_name.values():
        # This loop merges together consecutive shifts
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
        help='Your first name (as it appears on the consultant schedule)')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    raw_schedule = fetch_latest_schedule(args.host, args.port,
                                         args.username, args.password)
    schedule = build_schedule(raw_schedule)
    calendar = CalendarApi.authorize()
    for shift in schedule[args.name]:
        calendar.create_event(shift[0], shift[1])
