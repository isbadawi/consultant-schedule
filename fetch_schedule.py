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
    num = M.search(None, *criteria)[1][0].split()[-1]
    raw_email = M.fetch(num, '(RFC822)')[1][0][1]
    message = email.message_from_string(raw_email)
    raw_attachment = message.get_payload(1).get_payload()
    return base64.b64decode(raw_attachment)

def index_by_day(lines):
    """
    Maps days (Monday is 0) to lists of lines like '<start>-<end> <name>'.
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
        'Saturday', 'Sunday']
    schedule_by_day = []
    for i, day in enumerate(days):
        index = lines.index(day)
        next_index = None
        if i < len(days) - 1:
            next_index = lines.index(days[i + 1])
        schedule_by_day.append(lines[index + 1:next_index])
    return schedule_by_day

def merge_consecutive_shifts(schedule_by_name):
    for schedule in schedule_by_name.values():
        i = 1
        while i < len(schedule):
            previous_start, previous_end = schedule[i - 1]
            current_start, current_end = schedule[i]
            same_day = previous_start.day == current_start.day
            consecutive = previous_end.hour == current_start.hour
            if same_day and consecutive:
                schedule.insert(i - 1, (previous_start, current_end))
                del schedule[i]
                del schedule[i]
            else:
                i += 1

def shift_to_datetime_pair(week_day, shift):
    start_time = time(hour=int(shift.split('-')[0]))
    start_datetime = datetime.combine(week_day, start_time)
    shift = (start_datetime, start_datetime + timedelta(hours=2))
    return shift

def index_by_name(week_start, schedule_by_day):
    """
    Maps consultant names to lists of (start, end) tuples,
    where start and end are datetime objects.
    """
    schedule_by_name = collections.defaultdict(list)
    for i, shifts in enumerate(schedule_by_day):
        week_day = week_start + timedelta(days=i)
        for shift in shifts:
            shift, name = shift.split()
            shift = shift_to_datetime_pair(week_day, shift)
            schedule_by_name[name].append(shift)
    merge_consecutive_shifts(schedule_by_name)
    return schedule_by_name

def get_lines(s):
    lines = []
    for l in s.replace('\r\t', '\n').split('\n'):
        line = l.strip(' \r\t')
        if line:
            lines.append(line)
    return lines

def build_schedule(raw_schedule):
    lines = get_lines(raw_schedule)
    week_date = get_monday_date(lines[0])
    schedule_by_day = index_by_day(lines)
    schedule_by_name = index_by_name(week_date, schedule_by_day)
    return schedule_by_name

def populate_calendar(schedule):
    calendar = CalendarApi.authorize()
    colors = calendar.get_available_colors()
    for ((name, shifts), color) in zip(schedule.items(), colors):
        for shift in shifts:
            calendar.create_event(name, color, shift[0], shift[1])

def parse_args():
    parser = argparse.ArgumentParser(
        description='manage SOCS consultant schedule',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--host', default='exchange.mcgill.ca', metavar='host',
        help='IMAP host to fetch from')
    parser.add_argument('--port', default=993, type=int, metavar='port',
        help='IMAP port')
    parser.add_argument('--username', required=True, metavar='user',
        help='IMAP username')
    parser.add_argument('--password', required=True, metavar='pass',
        help='IMAP password')
    return parser.parse_args()

def main():
    args = parse_args()
    raw_schedule = fetch_latest_schedule(args.host, args.port,
        args.username, args.password)
    schedule = build_schedule(raw_schedule)
    populate_calendar(schedule)

if __name__ == '__main__':
    main()
