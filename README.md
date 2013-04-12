This is a utility for McGill SOCS lab consultants. It inspects your McGill inbox for the latest
lab consultant schedule, and populates a Google Calendar with the information.

To run this, install the requirements

    pip install -r requirements.txt
    
and run `fetch_schedule.py` with appropriate arguments.

    usage: fetch_schedule.py [-h] [--host host] [--port port] --username user
                             --password pass

    manage SOCS consultant schedule

    optional arguments:
      -h, --help       show this help message and exit
      --host host      IMAP host to fetch from (default: exchange.mcgill.ca)
      --port port      IMAP port (default: 993)
      --username user  IMAP username (default: None)
      --password pass  IMAP password (default: None)
