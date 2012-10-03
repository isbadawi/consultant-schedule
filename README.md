This script inspects your McGill inbox for emails from Faiyaz with the
latest lab consultant schedule, and creates corresponding events in your
Google Calendar.

To run this, you need

- Your McGill email and password
    You can pass these in to the command line, or set the
    MCGILL_SID and MCGILL_PIN environment variables

- Authorize this app to manipulate your Google calendar
    The first time this runs, a web browser will open and you'll be
    asked to authorize this app to touch your calendar. (It just creates
    events; nothing sneaky.)
