This script inspects your McGill inbox for emails from Faiyaz with the
latest lab consultant schedule, and creates corresponding events in your
Google Calendar.

To run this, install the requirements

    sudo pip install -r requirements.txt
    
and run `fetch_schedule.py` with appropriate arguments.

    usage: fetch_schedule.py [-h] [--host host] [--port port] --username user
                             --password pass --name name

    manage SOCS consultant schedule

    optional arguments:
      -h, --help       show this help message and exit
      --host host      IMAP host to fetch from (default: exchange.mcgill.ca)
      --port port      IMAP port (default: 993)
      --username user  IMAP username (default: None)
      --password pass  IMAP password (default: None)
      --name name      Your first name (as it appears on the consultant schedule))
                       (default: None)
